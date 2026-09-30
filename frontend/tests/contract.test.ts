/**
 * The shapes this console expects, checked against what the deployed contract
 * actually answered.
 *
 * tests/fixtures/chain.json was captured from
 * 0x10c063637F0b8cE8DDaeF75c4f856Eaaa44D26dE on StudioNet, by reading each view.
 * If the contract changes what it returns, these fail here rather than leaving a
 * page rendering "undefined".
 */
import { describe, expect, it } from "vitest";

import chain from "./fixtures/chain.json";
import {
  checkSchema,
  pageOf,
  protocolInfoSchema,
  protocolSchema,
  evidenceSchema,
  transitionSchema,
  verificationSchema,
  PAYABLE_METHODS,
  REQUIRED_METHODS,
} from "@/lib/genlayer/contract";
import schemaFile from "@/lib/genlayer/trace-schema.json";

describe("what the contract answers", () => {
  it("parses a page of protocols", () => {
    const parsed = pageOf(protocolSchema).safeParse(chain.list_protocols);
    if (!parsed.success) throw new Error(JSON.stringify(parsed.error.issues.slice(0, 4), null, 1));
    expect(parsed.data.items.length).toBeGreaterThan(0);
  });

  it("parses a protocol whichever client encoded it", () => {
    // genlayer-py returns a large integer as a number and genlayer-js returns
    // it as a decimal string; a console that only understood one of them would
    // work in tests and fail in the browser, which is what happened
    const parsed = protocolSchema.safeParse(chain.protocol_from_browser_client);
    if (!parsed.success) throw new Error(JSON.stringify(parsed.error.issues.slice(0, 4), null, 1));
    expect(parsed.data.definition?.economic_policy.enabled).toBe(true);
  });

  it("parses the protocol info", () => {
    const parsed = protocolInfoSchema.safeParse(chain.get_protocol_info);
    if (!parsed.success) throw new Error(JSON.stringify(parsed.error.issues.slice(0, 4), null, 1));
    expect(parsed.data.version).toBe("TRACE-1.0.0");
    expect(parsed.data.rules).toBe("TRACE-AGG-1");
  });

  it("parses a verification, with its findings and what each node found", () => {
    const parsed = verificationSchema.safeParse(chain.get_verification);
    if (!parsed.success) throw new Error(JSON.stringify(parsed.error.issues.slice(0, 4), null, 1));
    expect(parsed.data.findings.length).toBeGreaterThan(0);
    for (const finding of parsed.data.findings) {
      expect(["SATISFIED", "UNSATISFIED", "UNCERTAIN"]).toContain(finding.status);
      expect(["SATISFIED", "UNSATISFIED", "UNCERTAIN"]).toContain(finding.effective_status);
    }
    for (const item of parsed.data.evidence) {
      expect(["READ", "MISSING", "UNREADABLE"]).toContain(item.availability);
    }
  });

  it("parses evidence, history and activity", () => {
    expect(pageOf(evidenceSchema).safeParse(chain.list_evidence).success).toBe(true);
    expect(pageOf(transitionSchema).safeParse(chain.get_history).success).toBe(true);
    expect(pageOf(transitionSchema).safeParse(chain.list_activity).success).toBe(true);
  });

  it("only records results this console knows how to show", () => {
    const parsed = pageOf(protocolSchema).parse(chain.list_protocols);
    const known = ["VERIFIED", "PARTIALLY_VERIFIED", "NOT_VERIFIED", "INCONCLUSIVE",
                   "PROTOCOL_DEVIATION", "NONE"];
    for (const protocol of parsed.items) expect(known).toContain(protocol.overall_result);
  });
});

describe("what this console calls", () => {
  it("matches the deployment's own schema, method for method", () => {
    expect(checkSchema(schemaFile.schema)).toEqual([]);
  });

  it("sends value to exactly one method", () => {
    const methods = schemaFile.schema.methods as Record<string, { payable?: boolean }>;
    const payable = Object.keys(methods).filter((name) => methods[name]?.payable);
    expect(payable).toEqual(PAYABLE_METHODS);
  });

  it("knows every method the deployment has", () => {
    const methods = Object.keys(schemaFile.schema.methods ?? {});
    const unknown = methods.filter((name) => !(name in REQUIRED_METHODS));
    expect(unknown).toEqual([]);
  });
});
