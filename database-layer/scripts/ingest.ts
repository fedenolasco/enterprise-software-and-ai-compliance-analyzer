import "dotenv/config";
import path from "node:path";
import { readdir, readFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { PrismaClient, AuditEventType, AuditStatus, DocumentType, RiskCategory, RiskSeverity, RiskTier, SubscriptionStatus } from "@prisma/client";
import { Client } from "pg";
import { z } from "zod";
import { chunkText, inferRisk, readTextFile, resolveDataPath } from "../src/document-utils.js";
import { createEmbedding, toPgvectorLiteral } from "../src/embedding.js";

const vendorSchema = z.object({
  vendorCode: z.string(),
  name: z.string(),
  legalName: z.string(),
  headquartersCountry: z.string(),
  website: z.string().url().optional(),
  aiRiskTier: z.nativeEnum(RiskTier),
  aiProcessingNotes: z.string().optional()
});

const softwareSchema = z.object({
  softwareCode: z.string(),
  vendorCode: z.string(),
  name: z.string(),
  category: z.string(),
  deploymentModel: z.string(),
  aiCapabilitySummary: z.string().optional(),
  isBusinessCritical: z.boolean()
});

const subscriptionSchema = z.object({
  subscriptionCode: z.string(),
  vendorCode: z.string(),
  softwareCode: z.string(),
  department: z.string(),
  contractOwner: z.string(),
  billingCycle: z.string(),
  seatsPurchased: z.number().int().nonnegative(),
  seatsAssigned: z.number().int().nonnegative(),
  annualCostUsd: z.number().nonnegative(),
  monthlyCostUsd: z.number().nonnegative(),
  renewalDate: z.string(),
  autoRenews: z.boolean(),
  status: z.nativeEnum(SubscriptionStatus),
  cancellationNoticeDays: z.number().int().nonnegative()
});

const fixtureSchema = z.object({
  vendors: z.array(vendorSchema),
  software: z.array(softwareSchema),
  subscriptions: z.array(subscriptionSchema)
});

const prisma = new PrismaClient();

async function main() {
  const fixturePath = resolveDataPath("subscriptions.json");
  const rawFixture = await readFile(fixturePath, "utf8");
  const fixture = fixtureSchema.parse(JSON.parse(rawFixture));

  const pgClient = new Client({ connectionString: process.env.DATABASE_URL });
  await pgClient.connect();
  await pgClient.query("CREATE EXTENSION IF NOT EXISTS vector;");

  const vendorIdByCode = new Map<string, string>();
  const softwareIdByCode = new Map<string, string>();
  const subscriptionIdByCode = new Map<string, string>();

  for (const vendor of fixture.vendors) {
    const record = await prisma.vendor.upsert({
      where: { vendorCode: vendor.vendorCode },
      update: {
        name: vendor.name,
        legalName: vendor.legalName,
        headquartersCountry: vendor.headquartersCountry,
        website: vendor.website,
        aiRiskTier: vendor.aiRiskTier,
        aiProcessingNotes: vendor.aiProcessingNotes
      },
      create: vendor
    });

    vendorIdByCode.set(vendor.vendorCode, record.id);
  }

  for (const software of fixture.software) {
    const vendorId = vendorIdByCode.get(software.vendorCode);

    if (!vendorId) {
      throw new Error(`Missing vendor for software ${software.softwareCode}`);
    }

    const record = await prisma.software.upsert({
      where: { softwareCode: software.softwareCode },
      update: {
        vendorId,
        name: software.name,
        category: software.category,
        deploymentModel: software.deploymentModel,
        aiCapabilitySummary: software.aiCapabilitySummary,
        isBusinessCritical: software.isBusinessCritical
      },
      create: {
        softwareCode: software.softwareCode,
        vendorId,
        name: software.name,
        category: software.category,
        deploymentModel: software.deploymentModel,
        aiCapabilitySummary: software.aiCapabilitySummary,
        isBusinessCritical: software.isBusinessCritical
      }
    });

    softwareIdByCode.set(software.softwareCode, record.id);
  }

  for (const subscription of fixture.subscriptions) {
    const vendorId = vendorIdByCode.get(subscription.vendorCode);
    const softwareId = softwareIdByCode.get(subscription.softwareCode);

    if (!vendorId || !softwareId) {
      throw new Error(`Missing relation for subscription ${subscription.subscriptionCode}`);
    }

    const record = await prisma.subscription.upsert({
      where: { subscriptionCode: subscription.subscriptionCode },
      update: {
        vendorId,
        softwareId,
        department: subscription.department,
        contractOwner: subscription.contractOwner,
        billingCycle: subscription.billingCycle,
        seatsPurchased: subscription.seatsPurchased,
        seatsAssigned: subscription.seatsAssigned,
        annualCostUsd: subscription.annualCostUsd,
        monthlyCostUsd: subscription.monthlyCostUsd,
        renewalDate: new Date(subscription.renewalDate),
        autoRenews: subscription.autoRenews,
        status: subscription.status,
        cancellationNoticeDays: subscription.cancellationNoticeDays,
        lastValidatedAt: new Date()
      },
      create: {
        subscriptionCode: subscription.subscriptionCode,
        vendorId,
        softwareId,
        department: subscription.department,
        contractOwner: subscription.contractOwner,
        billingCycle: subscription.billingCycle,
        seatsPurchased: subscription.seatsPurchased,
        seatsAssigned: subscription.seatsAssigned,
        annualCostUsd: subscription.annualCostUsd,
        monthlyCostUsd: subscription.monthlyCostUsd,
        renewalDate: new Date(subscription.renewalDate),
        autoRenews: subscription.autoRenews,
        status: subscription.status,
        cancellationNoticeDays: subscription.cancellationNoticeDays,
        lastValidatedAt: new Date()
      }
    });

    subscriptionIdByCode.set(subscription.subscriptionCode, record.id);
  }

  const documentDirectory = resolveDataPath("documents");
  const documentFiles = (await readdir(documentDirectory)).filter((name) => name.endsWith(".txt"));

  for (const fileName of documentFiles) {
    const absolutePath = path.resolve(documentDirectory, fileName);
    const content = await readTextFile(absolutePath);
    const metadata = inferDocumentMetadata(fileName);
    const vendorId = metadata.vendorCode ? vendorIdByCode.get(metadata.vendorCode) ?? null : null;
    const softwareId = metadata.softwareCode ? softwareIdByCode.get(metadata.softwareCode) ?? null : null;

    const document = await prisma.complianceDocument.upsert({
      where: { sourcePath: absolutePath },
      update: {
        documentCode: metadata.documentCode,
        vendorId,
        softwareId,
        title: metadata.title,
        documentType: metadata.documentType,
        reviewStatus: "ingested"
      },
      create: {
        documentCode: metadata.documentCode,
        vendorId,
        softwareId,
        title: metadata.title,
        documentType: metadata.documentType,
        sourcePath: absolutePath,
        reviewStatus: "ingested"
      }
    });

    await prisma.documentChunk.deleteMany({ where: { documentId: document.id } });

    const chunks = chunkText(content);

    for (const chunk of chunks) {
      const risk = inferRisk(chunk.chunkText);
      const chunkRecord = await prisma.documentChunk.create({
        data: {
          documentId: document.id,
          chunkIndex: chunk.chunkIndex,
          chunkText: chunk.chunkText,
          tokenCount: chunk.tokenCount,
          riskSummary: risk.summary,
          riskCategory: risk.category as RiskCategory,
          riskSeverity: risk.severity as RiskSeverity,
          riskScore: risk.score
        }
      });

      const vector = await createEmbedding(chunk.chunkText);
      await pgClient.query(
        'UPDATE "DocumentChunk" SET "embedding" = $1::vector WHERE "id" = $2::uuid',
        [toPgvectorLiteral(vector), chunkRecord.id]
      );

      if (vendorId || softwareId) {
        await prisma.complianceRisk.create({
          data: {
            riskCode: `RSK-${randomUUID()}`,
            vendorId,
            softwareId,
            subscriptionId: findSubscriptionForVendor(vendorIdByCode, subscriptionIdByCode, fixture.subscriptions, metadata.vendorCode),
            documentChunkId: chunkRecord.id,
            category: risk.category as RiskCategory,
            severity: risk.severity as RiskSeverity,
            title: `${risk.category} review for ${metadata.title}`,
            rationale: risk.summary,
            mitigationStatus: risk.severity === "LOW" ? "monitor" : "open"
          }
        });
      }
    }
  }

  await prisma.auditEvent.create({
    data: {
      eventType: AuditEventType.INGESTION,
      status: AuditStatus.SUCCESS,
      actor: "database-layer/scripts/ingest.ts",
      traceId: `trace-${randomUUID()}`,
      message: "Synthetic subscriptions and compliance documents ingested",
      detail: {
        vendors: fixture.vendors.length,
        software: fixture.software.length,
        subscriptions: fixture.subscriptions.length,
        documents: documentFiles.length
      }
    }
  });

  await pgClient.end();
  await prisma.$disconnect();
  console.log(`Ingested ${fixture.subscriptions.length} subscriptions and ${documentFiles.length} documents.`);
}

function inferDocumentMetadata(fileName: string) {
  const base = fileName.replace(/\.txt$/i, "");

  const definitions: Record<string, { documentCode: string; title: string; documentType: DocumentType; vendorCode?: string; softwareCode?: string }> = {
    "openai-enterprise-sla": {
      documentCode: "DOC-OPENAI-SLA-001",
      title: "OpenAI Enterprise SLA",
      documentType: DocumentType.SLA,
      vendorCode: "VND-OPENAI-001",
      softwareCode: "SW-OPENAI-CHATGPT-ENT"
    },
    "openai-gdpr-policy": {
      documentCode: "DOC-OPENAI-GDPR-001",
      title: "OpenAI GDPR Policy",
      documentType: DocumentType.GDPR_POLICY,
      vendorCode: "VND-OPENAI-001",
      softwareCode: "SW-OPENAI-CHATGPT-ENT"
    },
    "microsoft-copilot-dpa": {
      documentCode: "DOC-MS-DPA-001",
      title: "Microsoft 365 Copilot DPA",
      documentType: DocumentType.DPA,
      vendorCode: "VND-MICROSOFT-001",
      softwareCode: "SW-MS-COPILOT-M365"
    },
    "microsoft-copilot-ai-policy": {
      documentCode: "DOC-MS-AI-001",
      title: "Microsoft 365 Copilot Responsible AI Notice",
      documentType: DocumentType.AI_POLICY,
      vendorCode: "VND-MICROSOFT-001",
      softwareCode: "SW-MS-COPILOT-M365"
    },
    "notion-ai-sla": {
      documentCode: "DOC-NOTION-SLA-001",
      title: "Notion AI SLA",
      documentType: DocumentType.SLA,
      vendorCode: "VND-NOTION-001",
      softwareCode: "SW-NOTION-AI"
    },
    "notion-ai-gdpr-policy": {
      documentCode: "DOC-NOTION-GDPR-001",
      title: "Notion AI GDPR Policy",
      documentType: DocumentType.GDPR_POLICY,
      vendorCode: "VND-NOTION-001",
      softwareCode: "SW-NOTION-AI"
    },
    "vendor-risk-register": {
      documentCode: "DOC-RISK-REGISTER-001",
      title: "Synthetic Vendor Risk Register",
      documentType: DocumentType.SECURITY_ADDENDUM
    }
  };

  const metadata = definitions[base];

  if (!metadata) {
    throw new Error(`No document metadata mapping defined for ${fileName}`);
  }

  return metadata;
}

function findSubscriptionForVendor(
  vendorIdByCode: Map<string, string>,
  subscriptionIdByCode: Map<string, string>,
  subscriptions: Array<z.infer<typeof subscriptionSchema>>,
  vendorCode: string | undefined
) {
  if (!vendorCode || !vendorIdByCode.has(vendorCode)) {
    return null;
  }

  const match = subscriptions.find((subscription) => subscription.vendorCode === vendorCode);
  return match ? (subscriptionIdByCode.get(match.subscriptionCode) ?? null) : null;
}

main().catch(async (error) => {
  console.error("Ingestion failed", error);
  await prisma.$disconnect();
  process.exit(1);
});
