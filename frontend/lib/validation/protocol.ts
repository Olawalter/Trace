/**
 * The rules the create form enforces, which are the contract's rules.
 *
 * Every check here exists in contracts/trace.py as well. This copy is a
 * convenience -- a mistake shows while typing instead of costing a transaction
 * -- and never an authority: the contract checks all of it again, and the
 * contract is what binds.
 */

export const MAX_TITLE = 120;
export const MAX_DESCRIPTION = 2000;
export const MAX_SUBJECT = 200;
export const MAX_TEXT = 600;
export const MAX_URL = 400;
export const MAX_REQUIREMENTS = 10;
export const MIN_DEADLINE_AHEAD = 10 * 60;
export const MAX_DEADLINE_AHEAD = 366 * 24 * 3600;
export const MIN_RECOVERY_WINDOW = 3600;
export const MAX_RECOVERY_WINDOW = 90 * 24 * 3600;
export const MIN_AMOUNT = 10n ** 15n;

export const SOURCE_TYPES = ["PUBLICATION", "REGISTRY", "REPOSITORY", "REPORT", "STATEMENT",
                             "OTHER"] as const;
export const ACTIONS = ["REFUND", "RELEASE", "SPLIT"] as const;

const FENCE = /[<>]{3,}/;

export type RequirementDraft = {
  requirementId: string;
  description: string;
  verificationRule: string;
  mandatory: boolean;
  minSources: string;
};

export type Draft = {
  title: string;
  description: string;
  subject: string;
  subjectType: string;
  deadline: number;
  recoveryHours: string;
  requirements: RequirementDraft[];
  allowedDomains: string;
  minimumSources: string;
  requiredSourceTypes: string[];
  allowMultipleSources: boolean;
  contradictionPolicy: string;
  economic: boolean;
  reward: string;
  bond: string;
  verifiedPct: string;
  partialPct: string;
  notVerifiedAction: string;
  inconclusiveAction: string;
  timeoutAction: string;
};

export const blankRequirement = (index: number): RequirementDraft => ({
  requirementId: `R${index + 1}`,
  description: "",
  verificationRule: "",
  mandatory: true,
  minSources: "1",
});

export const blankDraft = (now: number): Draft => ({
  title: "",
  description: "",
  subject: "",
  subjectType: "SOFTWARE_RELEASE",
  deadline: now + 7 * 24 * 3600,
  recoveryHours: "24",
  requirements: [blankRequirement(0)],
  allowedDomains: "",
  minimumSources: "1",
  requiredSourceTypes: [],
  allowMultipleSources: true,
  contradictionPolicy: "UNCERTAIN",
  economic: false,
  reward: "0",
  bond: "0",
  verifiedPct: "100",
  partialPct: "50",
  notVerifiedAction: "REFUND",
  inconclusiveAction: "REFUND",
  timeoutAction: "REFUND",
});

export type Problems = Record<string, string>;

const text = (value: string, field: string, limit: number, problems: Problems, key: string) => {
  const clean = value.trim();
  if (!clean) problems[key] = `${field} cannot be empty`;
  else if (clean.length > limit) problems[key] = `${field} is longer than ${limit} characters`;
  else if (FENCE.test(clean)) {
    problems[key] = `${field} cannot contain three or more angle brackets in a row`;
  }
  return clean;
};

/** Everything the contract would refuse, checked before a transaction is spent. */
export function validateDraft(draft: Draft, now: number): Problems {
  const problems: Problems = {};
  text(draft.title, "A title", MAX_TITLE, problems, "title");
  text(draft.description, "A description", MAX_DESCRIPTION, problems, "description");
  text(draft.subject, "A subject", MAX_SUBJECT, problems, "subject");
  text(draft.subjectType, "A subject type", 60, problems, "subjectType");

  if (draft.requirements.length === 0) {
    problems.requirements = "A protocol needs at least one requirement";
  }
  if (draft.requirements.length > MAX_REQUIREMENTS) {
    problems.requirements = `A protocol holds at most ${MAX_REQUIREMENTS} requirements`;
  }
  if (draft.requirements.length > 0 && !draft.requirements.some((r) => r.mandatory)) {
    problems.requirements = "At least one requirement must be mandatory";
  }

  const seen = new Set<string>();
  const said = new Set<string>();
  draft.requirements.forEach((requirement, index) => {
    text(requirement.description, "A requirement", MAX_TEXT, problems,
         `requirements.${index}.description`);
    text(requirement.verificationRule, "A verification rule", MAX_TEXT, problems,
         `requirements.${index}.verificationRule`);
    if (!/^R\d{1,3}$/.test(requirement.requirementId)) {
      problems[`requirements.${index}.requirementId`] = "An id is R followed by digits";
    } else if (seen.has(requirement.requirementId)) {
      problems[`requirements.${index}.requirementId`] = "That id is already used";
    }
    seen.add(requirement.requirementId);
    const normalised = requirement.description.trim().toLowerCase().replace(/\s+/g, " ");
    if (normalised && said.has(normalised)) {
      problems[`requirements.${index}.description`] = "That repeats an earlier requirement";
    }
    said.add(normalised);
    const sources = Number(requirement.minSources);
    if (!Number.isInteger(sources) || sources < 1 || sources > 5) {
      problems[`requirements.${index}.minSources`] = "Between 1 and 5 independent sources";
    }
  });

  if (draft.deadline < now + MIN_DEADLINE_AHEAD) {
    problems.deadline = "The deadline must be at least 10 minutes ahead";
  } else if (draft.deadline > now + MAX_DEADLINE_AHEAD) {
    problems.deadline = "The deadline cannot be more than 366 days ahead";
  }

  const window = Number(draft.recoveryHours) * 3600;
  if (!Number.isFinite(window) || window < MIN_RECOVERY_WINDOW || window > MAX_RECOVERY_WINDOW) {
    problems.recoveryHours = "Between 1 hour and 90 days";
  }

  const minimum = Number(draft.minimumSources);
  if (!Number.isInteger(minimum) || minimum < 1) {
    problems.minimumSources = "At least one source";
  }
  if (!draft.allowMultipleSources && minimum > 1) {
    problems.minimumSources = "This policy accepts one source, so it cannot require more than one";
  }
  for (const domain of splitDomains(draft.allowedDomains)) {
    if (!/^[a-z0-9.-]+\.[a-z0-9-]+$/.test(domain)) {
      problems.allowedDomains = `${domain} is not a host this contract can match`;
    }
  }

  if (draft.economic) {
    const reward = toAttoOrNull(draft.reward);
    const bond = toAttoOrNull(draft.bond);
    if (reward === null) problems.reward = "An amount in GEN, like 0.02";
    if (bond === null) problems.bond = "An amount in GEN, like 0.01";
    if (reward !== null && bond !== null) {
      if (reward === 0n && bond === 0n) {
        problems.reward = "An economic consequence needs a reward, a bond, or both";
      }
      for (const [name, amount] of [["reward", reward], ["bond", bond]] as const) {
        if (amount > 0n && amount < MIN_AMOUNT) {
          problems[name] = "Between 0.001 GEN and 1,000,000 GEN";
        }
      }
    }
    const verified = Number(draft.verifiedPct);
    const partial = Number(draft.partialPct);
    for (const [key, value] of [["verifiedPct", verified], ["partialPct", partial]] as const) {
      if (!Number.isFinite(value) || value < 0 || value > 100) problems[key] = "Between 0 and 100";
    }
    if (Number.isFinite(verified) && Number.isFinite(partial) && partial > verified) {
      problems.partialPct = "A partial result cannot release more than a verified one";
    }
  }
  return problems;
}

export const splitDomains = (value: string): string[] =>
  value.split(/[\s,]+/).map((d) => d.trim().toLowerCase().replace(/^\./, "")).filter(Boolean);

export function toAttoOrNull(gen: string): bigint | null {
  const value = (gen ?? "").trim();
  if (!/^\d+(\.\d{1,18})?$/.test(value)) return null;
  const [whole, fraction = ""] = value.split(".");
  return BigInt(whole) * 10n ** 18n + BigInt(fraction.padEnd(18, "0"));
}

/** The draft, in the shape set_draft parses. */
export function draftJson(draft: Draft): string {
  const economic = draft.economic
    ? {
        enabled: true,
        bond_required: Number(toAttoOrNull(draft.bond) ?? 0n),
        reward_required: Number(toAttoOrNull(draft.reward) ?? 0n),
        verified_payout_bps: Math.round(Number(draft.verifiedPct) * 100),
        partial_payout_bps: Math.round(Number(draft.partialPct) * 100),
        not_verified_action: draft.notVerifiedAction,
        inconclusive_action: draft.inconclusiveAction,
        timeout_action: draft.timeoutAction,
      }
    : { enabled: false };

  return JSON.stringify({
    requirements: draft.requirements.map((r) => ({
      requirement_id: r.requirementId,
      description: r.description.trim(),
      verification_rule: r.verificationRule.trim(),
      mandatory: r.mandatory,
      min_sources: Number(r.minSources),
    })),
    evidence_policy: {
      allowed_domains: splitDomains(draft.allowedDomains),
      minimum_sources: Number(draft.minimumSources),
      required_source_types: draft.requiredSourceTypes,
      allow_multiple_sources: draft.allowMultipleSources,
      contradiction_policy: draft.contradictionPolicy,
    },
    economic_policy: economic,
    deadline: Math.floor(draft.deadline),
    recovery_window: Math.round(Number(draft.recoveryHours) * 3600),
  });
}

export type EvidenceDraft = {
  sourceUrl: string;
  sourceType: string;
  supports: string[];
  label: string;
};

export function validateEvidence(evidence: EvidenceDraft): Problems {
  const problems: Problems = {};
  const url = evidence.sourceUrl.trim();
  if (!url) problems.sourceUrl = "An address the validators will fetch";
  else if (!url.toLowerCase().startsWith("https://")) problems.sourceUrl = "Must be an https address";
  else if (url.length > MAX_URL) problems.sourceUrl = `Longer than ${MAX_URL} characters`;
  else {
    const host = url.slice("https://".length).split("/")[0].toLowerCase().replace(/\.$/, "");
    if (host.includes("@")) problems.sourceUrl = "An address cannot carry credentials";
    else if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) problems.sourceUrl = "Name a host, not an IP address";
    else if (host === "localhost") problems.sourceUrl = "Must be a public address";
    else if (!host.includes(".")) problems.sourceUrl = "That address has no valid host";
    else if (!/^[a-z0-9.-]+$/.test(host)) problems.sourceUrl = "Punycode an international name first";
  }
  if (evidence.supports.length === 0) {
    problems.supports = "Name the requirements this evidence speaks to";
  }
  if (!SOURCE_TYPES.includes(evidence.sourceType as (typeof SOURCE_TYPES)[number])) {
    problems.sourceType = "Choose what kind of source this is";
  }
  if (evidence.label && FENCE.test(evidence.label)) {
    problems.label = "A label cannot contain three or more angle brackets in a row";
  }
  return problems;
}

export function evidenceJson(evidence: EvidenceDraft): string {
  return JSON.stringify({
    source_url: evidence.sourceUrl.trim(),
    source_type: evidence.sourceType,
    supports: [...evidence.supports].sort(),
    label: evidence.label.trim(),
  });
}

/**
 * Who published an address, counted the way the contract counts it: two pages
 * from one account are one source. Shown while typing so somebody can see they
 * are about to register a second page from the same voice.
 */
export function publisherOf(url: string): string {
  const match = /^https:\/\/([^/]+)(\/[^?#]*)?/i.exec((url ?? "").trim());
  if (!match) return "";
  const host = match[1].toLowerCase().replace(/\.$/, "");
  const path = match[2] ?? "";
  const bare = host.startsWith("www.") ? host.slice(4) : host;
  for (const [pages, label] of [["github.io", "github"], ["gitlab.io", "gitlab"]] as const) {
    if (bare.endsWith(`.${pages}`)) return `${label}:${bare.split(".")[0]}`;
  }
  const accounts: Record<string, string> = {
    "github.com": "github",
    "raw.githubusercontent.com": "github",
    "gist.github.com": "github",
    "gitlab.com": "gitlab",
    "bitbucket.org": "bitbucket",
    "medium.com": "medium",
    "substack.com": "substack",
    "npmjs.com": "npm",
    "pypi.org": "pypi",
  };
  for (const [known, label] of Object.entries(accounts)) {
    if (bare === known || bare.endsWith(`.${known}`)) {
      const account = path.split("/").filter(Boolean)[0]?.toLowerCase() ?? "";
      return account ? `${label}:${account}` : label;
    }
  }
  const multi = new Set(["co.uk", "com.au", "co.jp", "com.br", "co.nz", "co.za", "com.sg",
                         "org.uk", "ac.uk", "gov.uk", "com.mx", "co.in", "com.tr", "co.kr"]);
  const labels = bare.split(".");
  if (labels.length >= 3 && multi.has(labels.slice(-2).join("."))) return labels.slice(-3).join(".");
  return labels.length >= 2 ? labels.slice(-2).join(".") : bare;
}
