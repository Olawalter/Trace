import type { NextConfig } from "next";

/**
 * No server, no rewrites, no route handlers: this console reads GenLayer from
 * the browser and signs with the person's wallet. There is nothing for a
 * backend to do.
 */
const config: NextConfig = {
  reactStrictMode: true,
};

export default config;
