/**
 * What the contract returns, and what this console is allowed to send it.
 *
 * The shapes below are checked at the boundary rather than trusted: a read that
 * does not look like a protocol is a bug worth seeing, not a page rendering
 * "undefined". The call builders are the only place a method name or an
 * argument order is written down, and REQUIRED_METHODS is compared against the
 * schema the chain reports, so a console pointed at an older deployment says so
 * instead of failing when somebody signs.
 */
import { z } from "zod";

import schemaFile from "./trace-schema.json";

/** Amounts arrive as decimal strings; some readers hand back numbers. */
const atto = z.union([z.number(), z.string().regex(/^\d+$/)]).transform(String);
const seconds = z.union([z.number(), z.string().regex(/^\d+$/)]).transform(Number);

export const requirementSchema = z.object({
  requirement_id: z.string(),
  description: z.string(),
  verification_rule: z.string(),
  mandatory: z.boolean(),
  min_sources: z.number(),
});

export const evidencePolicySchema = z.object({
  allowed_domains: z.array(z.string()),
  minimum_sources: z.number(),
  required_source_types: z.array(z.string()),
  allow_multiple_sources: z.boolean(),
  contradiction_policy: z.string(),
});

export const economicPolicySchema = z.object({
  enabled: z.boolean(),
  // a large integer inside the frozen definition arrives as a number from one
  // client and as a decimal string from another, so accept both rather than
  // decide which client somebody must use
  bond_required: atto.optional(),
  reward_required: atto.optional(),
  verified_payout_bps: seconds.optional(),
  partial_payout_bps: seconds.optional(),
  not_verified_action: z.string().optional(),
  inconclusive_action: z.string().optional(),
  timeout_action: z.string().optional(),
});

export const definitionSchema = z.object({
  requirements: z.array(requirementSchema),
  evidence_policy: evidencePolicySchema,
  economic_policy: economicPolicySchema,
  deadline: seconds,
  recovery_window: seconds,
  rules: z.string(),
});

export const protocolSchema = z.object({
  protocol_id: z.string(),
  creator: z.string(),
  title: z.string(),
  description: z.string(),
  subject: z.string(),
  subject_type: z.string(),
  lifecycle: z.string(),
  overall_result: z.string(),
  fingerprint: z.string(),
  economic: z.boolean(),
  bond_required: atto,
  bond_deposited: atto,
  reward_required: atto,
  reward_deposited: atto,
  paid_creator: atto,
  // what the bond side was paid. Not "paid to whoever submitted evidence":
  // submitting evidence carries no claim on the money
  paid_bond_depositor: atto,
  // the account the creator named as answerable, frozen with the definition
  responsible_party: z.string(),
  // the account whose transaction actually paid the bond. Empty until it does
  bond_depositor: z.string(),
  accepted_at: seconds,
  deadline: seconds,
  recovery_window: seconds,
  created_at: seconds,
  activated_at: seconds,
  updated_at: seconds,
  settled_at: seconds,
  evidence_count: seconds,
  round_count: seconds,
  last_round_at: seconds,
  latest_verification_id: z.string(),
  definition: definitionSchema.nullable(),
  frozen: z.boolean(),
});

export const evidenceSchema = z.object({
  evidence_id: z.string(),
  protocol_id: z.string(),
  source_url: z.string(),
  source_type: z.string(),
  source_domain: z.string(),
  publisher: z.string(),
  supports: z.array(z.string()),
  label: z.string(),
  submitter: z.string(),
  submitted_at: seconds,
  status: z.string(),
});

export const findingSchema = z.object({
  requirement_id: z.string(),
  status: z.string(),
  effective_status: z.string(),
  independent_sources: z.number(),
  evidence_refs: z.array(z.string()),
  quote: z.string(),
  quote_evidence_id: z.string(),
  reason: z.string(),
});

export const observedSchema = z.object({
  evidence_id: z.string(),
  publisher: z.string(),
  availability: z.string(),
  observed_at: seconds,
  excerpt: z.string(),
  excerpt_digest: z.string(),
});

export const verificationSchema = z.object({
  verification_id: z.string(),
  protocol_id: z.string(),
  round: z.number(),
  status: z.string(),
  overall_result: z.string(),
  summary: z.string(),
  deviation: z.string(),
  held_for_sources: z.array(z.string()),
  findings: z.array(findingSchema),
  evidence: z.array(observedSchema),
  fingerprint: z.string(),
  rules: z.string(),
  submitted_at: seconds,
  verified_at: seconds,
  finalized_at: seconds,
  requested_by: z.string(),
});

export const transitionSchema = z.object({
  protocol_id: z.string(),
  from: z.string(),
  to: z.string(),
  result: z.string(),
  at: seconds,
  note: z.string(),
});

export const protocolInfoSchema = z.object({
  version: z.string(),
  rules: z.string(),
  protocol_count: z.number(),
  total_custody: atto,
  lifecycle_states: z.array(z.string()),
  results: z.array(z.string()),
  statuses: z.array(z.string()),
  source_types: z.array(z.string()),
  actions: z.array(z.string()),
  limits: z.record(z.string(), z.unknown()),
});

export const pageOf = <T extends z.ZodTypeAny>(item: T) =>
  z.object({ total: z.number(), items: z.array(item) });

export type Protocol = z.infer<typeof protocolSchema>;
export type Requirement = z.infer<typeof requirementSchema>;
export type Evidence = z.infer<typeof evidenceSchema>;
export type Verification = z.infer<typeof verificationSchema>;
export type Finding = z.infer<typeof findingSchema>;
export type Observed = z.infer<typeof observedSchema>;
export type Transition = z.infer<typeof transitionSchema>;
export type ProtocolInfo = z.infer<typeof protocolInfoSchema>;
export type Definition = z.infer<typeof definitionSchema>;

/** Every method this console calls, with how many arguments it sends. */
export const REQUIRED_METHODS: Record<string, number> = {
  create_protocol: 4,
  set_draft: 2,
  activate_protocol: 1,
  accept_protocol: 1,
  cancel_protocol: 1,
  fund_protocol: 1,
  submit_evidence: 2,
  request_verification: 1,
  accept_verification: 1,
  finalize_protocol: 1,
  recover_protocol: 1,
  get_protocol_info: 0,
  get_protocol: 1,
  list_protocols: 2,
  list_by_creator: 3,
  get_evidence: 2,
  list_evidence: 3,
  get_verification: 2,
  list_verifications: 3,
  get_history: 3,
  list_activity: 2,
};

/** The one method that receives GEN. Everything else must send none. */
export const PAYABLE_METHODS = ["fund_protocol"];

type SchemaMethod = { params?: unknown[]; readonly?: boolean; payable?: boolean };
type ChainSchema = { methods?: Record<string, SchemaMethod> };

/**
 * Compare what this console intends to call against what the deployment says it
 * has. A missing method or a changed arity means the console is pointed at a
 * different contract, and it should say so rather than discover it at signing.
 */
export function checkSchema(chain: ChainSchema | undefined): string[] {
  const methods = chain?.methods;
  if (!methods) return ["the contract did not report a schema"];
  const problems: string[] = [];
  for (const [name, arity] of Object.entries(REQUIRED_METHODS)) {
    const found = methods[name];
    if (!found) {
      problems.push(`the deployment has no ${name}`);
      continue;
    }
    const count = (found.params ?? []).length;
    if (count !== arity) {
      problems.push(`${name} takes ${count} argument(s) here and ${arity} in this console`);
    }
  }
  for (const name of PAYABLE_METHODS) {
    if (methods[name] && methods[name].payable !== true) {
      problems.push(`${name} is not payable in the deployment`);
    }
  }
  return problems;
}

/** The schema that was read from the deployment this console was built for. */
export const recordedSchema = schemaFile as {
  contract_address: string;
  read_at: string;
  schema: ChainSchema;
};

export type Call = { functionName: string; args: (string | number)[]; value: bigint };

const call = (functionName: string, args: (string | number)[] = [], value = 0n): Call => ({
  functionName,
  args,
  value,
});

/** Every write this console can compose, in one place. */
export const writes = {
  createProtocol: (title: string, description: string, subject: string, subjectType: string) =>
    call("create_protocol", [title, description, subject, subjectType]),
  setDraft: (protocolId: string, draftJson: string) => call("set_draft", [protocolId, draftJson]),
  activate: (protocolId: string) => call("activate_protocol", [protocolId]),
  // the responsible party taking the protocol on, which is a different act from
  // accepting a RESULT further down this list
  acceptProtocol: (protocolId: string) => call("accept_protocol", [protocolId]),
  cancel: (protocolId: string) => call("cancel_protocol", [protocolId]),
  fund: (protocolId: string, atto: bigint) => call("fund_protocol", [protocolId], atto),
  submitEvidence: (protocolId: string, evidenceJson: string) =>
    call("submit_evidence", [protocolId, evidenceJson]),
  requestVerification: (protocolId: string) => call("request_verification", [protocolId]),
  acceptResult: (protocolId: string) => call("accept_verification", [protocolId]),
  finalize: (protocolId: string) => call("finalize_protocol", [protocolId]),
  recover: (protocolId: string) => call("recover_protocol", [protocolId]),
};

/** Every read, with the shape each answer is checked against. */
export const reads = {
  info: { functionName: "get_protocol_info", args: [] as (string | number)[], schema: protocolInfoSchema },
  protocol: (id: string) => ({ functionName: "get_protocol", args: [id], schema: protocolSchema }),
  protocols: (offset = 0, limit = 20) => ({
    functionName: "list_protocols",
    args: [offset, limit],
    schema: pageOf(protocolSchema),
  }),
  byCreator: (creator: string, offset = 0, limit = 20) => ({
    functionName: "list_by_creator",
    args: [creator, offset, limit],
    schema: pageOf(protocolSchema),
  }),
  evidence: (id: string, offset = 0, limit = 30) => ({
    functionName: "list_evidence",
    args: [id, offset, limit],
    schema: pageOf(evidenceSchema),
  }),
  verification: (id: string, round: number) => ({
    functionName: "get_verification",
    args: [id, round],
    schema: verificationSchema,
  }),
  verifications: (id: string, offset = 0, limit = 10) => ({
    functionName: "list_verifications",
    args: [id, offset, limit],
    schema: pageOf(verificationSchema),
  }),
  history: (id: string, offset = 0, limit = 30) => ({
    functionName: "get_history",
    args: [id, offset, limit],
    schema: pageOf(transitionSchema),
  }),
  activity: (offset = 0, limit = 20) => ({
    functionName: "list_activity",
    args: [offset, limit],
    schema: pageOf(transitionSchema),
  }),
};
