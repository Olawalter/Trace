import { configResult } from "@/lib/config/env";

/**
 * When the console is not configured, say exactly which variable is wrong.
 * Guessing an address would be worse than refusing to run.
 */
export function ConfigProblem() {
  if (configResult.ok) return null;
  return (
    <section role="alert" className="card border-[var(--warning)] p-5">
      <h1 className="text-lg">TRACE is not configured</h1>
      <p className="mt-1 text-sm text-[var(--muted)]">
        This console reads one deployed contract and nothing else. Set these in
        <span className="mono"> frontend/.env.local</span> and restart it.
      </p>
      <table className="mt-4 w-full text-left text-sm">
        <thead className="label">
          <tr>
            <th className="pb-2 pr-4 font-normal">Variable</th>
            <th className="pb-2 pr-4 font-normal">Found</th>
            <th className="pb-2 font-normal">Wanted</th>
          </tr>
        </thead>
        <tbody className="mono text-xs">
          {configResult.problems.map((problem) => (
            <tr key={problem.name} className="border-t border-[var(--border)]">
              <td className="py-2 pr-4">{problem.name}</td>
              <td className="py-2 pr-4 text-[var(--error)]">{problem.found}</td>
              <td className="py-2 text-[var(--muted)]">{problem.wanted}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
