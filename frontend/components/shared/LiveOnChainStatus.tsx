import { Activity, ExternalLink, Globe2 } from "lucide-react";

const CONTRACT_ADDRESS = "0x9E71519cD8C72379caD79c6A6Fc5bf5FF261b149";
const CONTRACT_EXPLORER_URL = `https://scan.bohr.life/address/${CONTRACT_ADDRESS}`;

export function LiveOnChainStatus() {
  return (
    <section
      aria-labelledby="on-chain-status-title"
      className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#111714] p-5 text-white shadow-xl"
    >
      <div className="absolute -right-12 -top-12 h-32 w-32 rounded-full bg-[#7A9E7E]/15 blur-2xl" />
      <div className="relative">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#7A9E7E]/15 text-[#B8D5B8]">
              <Globe2 className="h-4.5 w-4.5" aria-hidden="true" />
            </span>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#B8D5B8]">
                Live On-Chain Status
              </p>
              <h2 id="on-chain-status-title" className="mt-0.5 text-base font-semibold text-white">
                BOT Chain Mainnet
              </h2>
            </div>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2.5 py-1 text-[10px] font-bold text-emerald-300">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_8px_rgba(110,231,183,0.9)]" />
            Active
          </span>
        </div>

        <div className="mt-5 grid gap-3 border-t border-white/10 pt-4 text-xs sm:grid-cols-[auto_1fr] sm:items-center">
          <span className="text-white/50">Network</span>
          <span className="font-medium text-white">BOT Chain Mainnet <span className="text-white/45">(Chain ID: 677)</span></span>
          <span className="text-white/50">Smart Contract</span>
          <a
            href={CONTRACT_EXPLORER_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-w-0 items-center gap-1.5 font-mono text-[11px] text-[#B8D5B8] transition-colors hover:text-white"
          >
            <span className="break-all">{CONTRACT_ADDRESS}</span>
            <ExternalLink className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
          </a>
          <span className="text-white/50">Status</span>
          <span className="inline-flex items-center gap-1.5 font-medium text-emerald-300">
            <Activity className="h-3.5 w-3.5" aria-hidden="true" />
            Verified &amp; Active On-Chain
          </span>
        </div>

        <a
          href={CONTRACT_EXPLORER_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-5 inline-flex items-center gap-2 text-xs font-bold text-white transition-colors hover:text-[#B8D5B8]"
        >
          View contract on BOT Explorer
          <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
        </a>
      </div>
    </section>
  );
}
