"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { z } from "zod";

import { FINAL, NON_FINAL, readClient, type Client } from "@/lib/genlayer/client";
import { checkSchema, reads, recordedSchema, type Call } from "@/lib/genlayer/contract";
import { readFailure } from "@/lib/genlayer/errors";
import { configResult } from "@/lib/config/env";
import { initialTx, runWrite, type TxState } from "@/lib/genlayer/transaction";

type Read<T> = { functionName: string; args: (string | number)[]; schema: z.ZodType<T> };

export type ReadState<T> = {
  data: T | undefined;
  error: string | undefined;
  loading: boolean;
  reload: () => void;
};

const LIST_POLL_MS = 120_000;
const DETAIL_POLL_MS = 120_000;

/**
 * Read one thing from the contract.
 *
 * `final` chooses which state to ask for: durable answers come from what
 * GenLayer has finalized, and the newest non-final state is used only while
 * following a write the person just sent.
 *
 * Polling pauses while the tab is hidden, but the first read always happens --
 * a page opened in a background tab must still load.
 */
export function useRead<T>(read: Read<T> | undefined, options: { pollMs?: number; final?: boolean } = {}):
  ReadState<T> {
  const { pollMs = 0, final = true } = options;
  const [data, setData] = useState<T>();
  const [error, setError] = useState<string>();
  const [settled, setSettled] = useState("");
  const [nonce, setNonce] = useState(0);
  const loadedOnce = useRef(false);

  const key = read ? `${read.functionName}:${JSON.stringify(read.args)}:${final}` : "";
  // derived rather than stored: a key that has not finished loading yet IS the
  // loading state, and storing it separately means an effect that sets state on
  // the way in, which costs a render and can drift out of step with the key
  const loading = Boolean(read) && configResult.ok && settled !== key;

  useEffect(() => {
    if (!read || !configResult.ok) return;
    let cancelled = false;

    const load = async () => {
      if (loadedOnce.current && typeof document !== "undefined" && document.hidden) return;
      try {
        const client = readClient();
        const answer = await client.readContract({
          address: configResult.ok ? configResult.config.contractAddress : "0x",
          functionName: read.functionName,
          args: read.args,
          transactionHashVariant: final ? FINAL : NON_FINAL,
        } as never);
        if (cancelled) return;
        const parsed = read.schema.safeParse(answer);
        if (!parsed.success) {
          // name the field: "a shape this console does not recognise" tells
          // nobody which shape, and this is exactly when somebody needs to know
          const first = parsed.error.issues[0];
          const where = first?.path?.join(".") || "the answer";
          setError(`The contract answered in a shape this console does not recognise ` +
                   `(${where}: ${first?.message ?? "unexpected"}).`);
        } else {
          setData(parsed.data);
          setError(undefined);
        }
      } catch (err) {
        if (!cancelled) setError(readFailure(err));
      } finally {
        if (!cancelled) {
          loadedOnce.current = true;
          setSettled(key);
        }
      }
    };

    void load();
    if (!pollMs) return () => { cancelled = true; };
    const timer = setInterval(load, pollMs);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, nonce, pollMs, final]);

  return { data, error, loading, reload: useCallback(() => setNonce((n) => n + 1), []) };
}

export const useProtocols = () => useRead(reads.protocols(0, 50), { pollMs: LIST_POLL_MS });
export const useActivity = () => useRead(reads.activity(0, 40), { pollMs: LIST_POLL_MS });
export const useInfo = () => useRead(reads.info);

export const useProtocol = (id: string | undefined, live = false) =>
  useRead(id ? reads.protocol(id) : undefined, { pollMs: DETAIL_POLL_MS, final: !live });

export const useEvidence = (id: string | undefined) =>
  useRead(id ? reads.evidence(id) : undefined, { pollMs: DETAIL_POLL_MS });

export const useHistory = (id: string | undefined) =>
  useRead(id ? reads.history(id) : undefined, { pollMs: DETAIL_POLL_MS });

export const useVerifications = (id: string | undefined, rounds: number) =>
  useRead(id && rounds > 0 ? reads.verifications(id) : undefined, { pollMs: DETAIL_POLL_MS });

/** Whether this console and the deployment agree about what the contract has. */
export function useDeployment() {
  const [problems, setProblems] = useState<string[] | undefined>();
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const client = readClient();
        const schema = (await client.getContractSchema({
          address: configResult.ok ? configResult.config.contractAddress : "0x",
        } as never)) as never;
        if (!cancelled) setProblems(checkSchema(schema));
      } catch {
        // the schema could not be read; the recorded one is what this console
        // was built against, and saying nothing is better than crying wolf
        if (!cancelled) setProblems(checkSchema(recordedSchema.schema));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);
  return problems;
}

/** A clock that ticks, so "in 3 minutes" stops being wrong while you read it. */
export function useNow(everyMs = 30_000) {
  const [now, setNow] = useState(() => Math.floor(Date.now() / 1000));
  useEffect(() => {
    const timer = setInterval(() => setNow(Math.floor(Date.now() / 1000)), everyMs);
    return () => clearInterval(timer);
  }, [everyMs]);
  return now;
}

export type SendOptions = {
  call: Call;
  /** Resolves true once the contract's own views show the write. */
  reconciled: () => Promise<boolean>;
  onRecorded?: () => void;
};

/** Send one write, and follow it honestly. */
export function useSend(provider: unknown, writeClientFor: (provider: unknown) => Client) {
  const [tx, setTx] = useState<TxState>(initialTx);
  const running = useRef(false);

  const send = useCallback(
    async (options: SendOptions) => {
      if (running.current || !configResult.ok) return;
      running.current = true;
      setTx({ ...initialTx, phase: "RUNNING" });
      try {
        await runWrite({
          config: configResult.config,
          client: writeClientFor(provider),
          poller: readClient(),
          call: options.call,
          reconciled: options.reconciled,
          onRecorded: options.onRecorded,
          onUpdate: setTx,
        });
      } finally {
        running.current = false;
      }
    },
    [provider, writeClientFor],
  );

  const reset = useCallback(() => setTx(initialTx), []);
  return useMemo(() => ({ tx, send, reset }), [tx, send, reset]);
}
