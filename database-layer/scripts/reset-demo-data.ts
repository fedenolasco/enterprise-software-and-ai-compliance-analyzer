import "dotenv/config";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  const confirmed = process.argv.includes("--yes") || process.env.RESET_DEMO_DATA === "true";

  if (!confirmed) {
    throw new Error(
      "Refusing to reset demo data without confirmation. Re-run with `-- --yes` or set RESET_DEMO_DATA=true."
    );
  }

  const before = await getCounts();

  const result = await prisma.$transaction(async (tx) => {
    const auditEvents = await tx.auditEvent.deleteMany();
    const complianceRisks = await tx.complianceRisk.deleteMany();
    const documentChunks = await tx.documentChunk.deleteMany();
    const complianceDocuments = await tx.complianceDocument.deleteMany();
    const subscriptions = await tx.subscription.deleteMany();
    const software = await tx.software.deleteMany();
    const vendors = await tx.vendor.deleteMany();

    return {
      auditEvents: auditEvents.count,
      complianceRisks: complianceRisks.count,
      documentChunks: documentChunks.count,
      complianceDocuments: complianceDocuments.count,
      subscriptions: subscriptions.count,
      software: software.count,
      vendors: vendors.count
    };
  });

  const after = await getCounts();

  console.log(
    JSON.stringify(
      {
        message: "Demo data reset completed",
        before,
        deleted: result,
        after
      },
      null,
      2
    )
  );
}

async function getCounts() {
  const [
    vendors,
    software,
    subscriptions,
    complianceDocuments,
    documentChunks,
    complianceRisks,
    auditEvents
  ] = await Promise.all([
    prisma.vendor.count(),
    prisma.software.count(),
    prisma.subscription.count(),
    prisma.complianceDocument.count(),
    prisma.documentChunk.count(),
    prisma.complianceRisk.count(),
    prisma.auditEvent.count()
  ]);

  return {
    vendors,
    software,
    subscriptions,
    complianceDocuments,
    documentChunks,
    complianceRisks,
    auditEvents
  };
}

main()
  .catch((error) => {
    console.error("Demo data reset failed", error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
