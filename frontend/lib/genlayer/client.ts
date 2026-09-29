/**
 * The only way this console talks to GenLayer.
 *
 * Two clients: one that reads without any wallet, and one that writes with the
 * account the person connected. Nothing here is cached beyond the client
 * objects themselves -- what the contract says is read from the contract.
 */
import { createClient, createAccount } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionHashVariant } from "genlayer-js/types";
import type { GenLayerClient, GenLayerChain } from "genlayer-js/types";

import { configResult, type AppConfig } from "@/lib/config/env";

export type Client = GenLayerClient<GenLayerChain>;

let reader: Client | undefined;

/** A client for reads. It has no account and can sign nothing. */
export function readClient(): Client {
  if (!configResult.ok) throw new Error("TRACE is not configured; see the notice on the page");
  if (!reader) {
    reader = createClient({ chain: studionet, account: createAccount() }) as Client;
  }
  return reader;
}

/** A client bound to the wallet's provider, for writes the person signs. */
export function writeClient(provider: unknown): Client {
  if (!configResult.ok) throw new Error("TRACE is not configured; see the notice on the page");
  return createClient({
    chain: studionet,
    // the wallet signs; this console never holds a key
    account: undefined,
    provider: provider as never,
  }) as Client;
}

export function appConfig(): AppConfig {
  if (!configResult.ok) throw new Error("TRACE is not configured");
  return configResult.config;
}

/**
 * Which state to read.
 *
 * A durable decision -- what a protocol's result is, what was paid -- is read
 * from state GenLayer has finalized. The newest non-final state is used only to
 * follow a write the person just sent, and is labelled as such wherever it is
 * shown.
 *
 * The parameter is `transactionHashVariant`, not `state`: readContract in
 * genlayer-js 1.1.8 has no `state`, and passing one is silently ignored, which
 * is a good way to believe you are reading final state when you are not.
 */
export const FINAL = TransactionHashVariant.LATEST_FINAL;
export const NON_FINAL = TransactionHashVariant.LATEST_NONFINAL;
