import Link from "next/link";
import { ExternalLink } from "lucide-react";

const quickLinks = [
  { label: "How It Works", href: "/#how-it-works" },
  { label: "For Caregivers", href: "/#for-caregivers" },
  { label: "Trust & Safety", href: "/#trust" },
];

export default function Footer() {
  return (
    <footer
      className="border-t border-[#445348] text-white/75"
      style={{ backgroundColor: "#1E231D" }}
    >
      <div className="mx-auto max-w-7xl px-6 py-12 lg:px-8">
        <div className="grid gap-10 md:grid-cols-3 md:gap-12">
          <div className="max-w-md">
            <Link
              href="/"
              className="inline-flex items-center gap-3 text-xl font-bold tracking-[0.18em] text-white transition-colors hover:text-[#B8D5B8]"
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#7A9E7E] text-sm tracking-normal text-white">
                T
              </span>
              TIARA
            </Link>
            <p className="mt-4 max-w-sm text-sm leading-6 text-white/65">
              AI Cognitive Care Platform &amp; On-Chain Wisdom Log for Dementia Caregivers.
            </p>
            <p className="mt-4 text-xs leading-5 text-white/45">
              Not a medical diagnosis tool. For informational and caregiver support purposes only.
            </p>
          </div>

          <nav aria-label="Footer navigation" className="md:justify-self-center">
            <h2 className="text-xs font-semibold uppercase tracking-[0.18em] text-[#B8D5B8]">
              Explore
            </h2>
            <ul className="mt-4 space-y-3 text-sm text-white/65">
              {quickLinks.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="transition-colors hover:text-white">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <div className="md:justify-self-end">
            <h2 className="text-xs font-semibold uppercase tracking-[0.18em] text-[#B8D5B8]">
              On-chain verification
            </h2>
            <a
              href="https://botchain.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex h-12 items-center"
            >
              <img
                src="/Asset4.png"
                alt="BOT Chain"
                className="h-10 w-auto max-w-[180px] object-contain"
              />
            </a>
            <p className="mt-4 text-sm text-white/65">
              Powered by{" "}
              <a
                href="https://botchain.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="font-semibold text-[#B8D5B8] transition-colors hover:text-white"
              >
                BOT Chain
              </a>
            </p>
            <a
              href="https://scan.bohr.life/address/0x9E71519cD8C72379caD79c6A6Fc5bf5FF261b149"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex max-w-full items-center gap-2 rounded-lg border border-[#7A9E7E] bg-[#2B382D] px-4 py-3 text-sm font-semibold text-white transition-all hover:border-[#B8D5B8] hover:bg-[#3A4B3D]"
            >
              Verify Contract on BOT Mainnet
              <ExternalLink className="h-4 w-4" aria-hidden="true" />
            </a>
          </div>
        </div>

        <div className="mt-10 flex flex-col gap-3 border-t border-white/10 pt-6 text-xs text-white/40 sm:flex-row sm:items-center sm:justify-between">
          <p>&copy; 2026 TIARA Platform. All rights reserved.</p>
          <p>Built for thoughtful, connected care.</p>
        </div>
      </div>
    </footer>
  );
}