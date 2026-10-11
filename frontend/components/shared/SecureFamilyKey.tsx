import { KeyRound, ShieldCheck } from "lucide-react";

export function SecureFamilyKey() {
  return (
    <section
      aria-labelledby="secure-family-key-title"
      className="rounded-2xl border border-accent/25 bg-[#16302f] p-6 text-white shadow-sm"
    >
      <div className="flex items-start gap-3.5">
        <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-[#B8D5B8]/15 text-[#B8D5B8]">
          <KeyRound className="h-5 w-5" aria-hidden="true" />
        </span>
        <div>
          <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-[#B8D5B8]">
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
            Privacy layer
          </div>
          <h2 id="secure-family-key-title" className="mt-1 text-lg font-bold font-serif-editorial">
            Web3 Secure Family Key Protection
          </h2>
        </div>
      </div>
      <p className="mt-4 text-sm leading-relaxed text-white/75">
        Cognitive health history is highly sensitive. TIARA uses a crypto wallet (Web3 Wallet) not just for login, but as the Family&apos;s Absolute Access Key (Secure Family Key). Only an authorized family wallet holding the valid private key can decrypt and view cognitive progress reports privately and securely, without relying on a vulnerable central server.
      </p>
    </section>
  );
}
