import "dotenv/config";
import { randomUUID } from "node:crypto";
import { PrismaClient, AuditEventType, AuditStatus } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  const target = await prisma.subscription.findFirst({ orderBy: { createdAt: "asc" } });

  if (!target) {
    throw new Error("No subscriptions found. Run the ingestion step first.");
  }

  const roundsPerWorker = 5;
  const workerCount = 4;

  const workers = Array.from({ length: workerCount }, (_, workerIndex) =>
    runWorker(workerIndex + 1, target.id, roundsPerWorker)
  );

  const results = await Promise.all(workers);
  const refreshed = await prisma.subscription.findUniqueOrThrow({ where: { id: target.id } });

  await prisma.auditEvent.create({
    data: {
      eventType: AuditEventType.WRITE_VALIDATION,
      status: AuditStatus.SUCCESS,
      actor: "database-layer/scripts/validate-concurrency.ts",
      traceId: `trace-${randomUUID()}`,
      subscriptionId: target.id,
      message: "Concurrent validation completed",
      detail: {
        workerCount,
        roundsPerWorker,
        attempts: results.reduce((sum, item) => sum + item.attempts, 0),
        successes: results.reduce((sum, item) => sum + item.successes, 0),
        finalRowVersion: refreshed.rowVersion,
        finalSeatsAssigned: refreshed.seatsAssigned
      }
    }
  });

  console.log(JSON.stringify({
    subscriptionCode: refreshed.subscriptionCode,
    finalRowVersion: refreshed.rowVersion,
    finalSeatsAssigned: refreshed.seatsAssigned,
    workers: results
  }, null, 2));

  await prisma.$disconnect();
}

async function runWorker(workerNumber: number, subscriptionId: string, rounds: number) {
  let attempts = 0;
  let successes = 0;

  for (let round = 0; round < rounds; round += 1) {
    attempts += 1;
    const current = await prisma.subscription.findUniqueOrThrow({ where: { id: subscriptionId } });

    const seatDelta = (workerNumber + round) % 2 === 0 ? 1 : 0;
    const updateResult = await prisma.subscription.updateMany({
      where: {
        id: subscriptionId,
        rowVersion: current.rowVersion
      },
      data: {
        seatsAssigned: Math.min(current.seatsPurchased, current.seatsAssigned + seatDelta),
        rowVersion: { increment: 1 },
        lastValidatedAt: new Date()
      }
    });

    if (updateResult.count > 0) {
      successes += 1;
    }

    await prisma.auditEvent.create({
      data: {
        eventType: updateResult.count > 0 ? AuditEventType.WRITE_VALIDATION : AuditEventType.READ_VALIDATION,
        status: AuditStatus.SUCCESS,
        actor: `concurrency-worker-${workerNumber}`,
        subscriptionId,
        traceId: `trace-${randomUUID()}`,
        message: updateResult.count > 0 ? "Optimistic concurrency update applied" : "Stale row version detected and skipped",
        detail: {
          round,
          observedRowVersion: current.rowVersion,
          seatDelta,
          updateApplied: updateResult.count > 0
        }
      }
    });
  }

  return { workerNumber, attempts, successes };
}

main().catch(async (error) => {
  console.error("Concurrency validation failed", error);
  await prisma.$disconnect();
  process.exit(1);
});
