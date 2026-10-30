import Link from "next/link";

const quickLinks = [
  { label: "Cara Kerja", href: "/#how-it-works" },
  { label: "Untuk Caregiver", href: "/#for-caregivers" },
  { label: "Kepercayaan & Keamanan", href: "/#trust" },
];

export default function Footer() {
  return (
    <footer
      className="border-t border-[#445348] text-white/75"
      style={{ backgroundColor: "#1E231D" }}
    >
      <div className="mx-auto max-w-7xl px-6 py-12 lg:px-8">
        <div className="grid gap-10 md:grid-cols-2 md:gap-12">
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
              Platform Perawatan Kognitif AI &amp; Panduan Demensia untuk Caregiver.
            </p>
            <p className="mt-4 text-xs leading-5 text-white/45">
              Bukan alat diagnosis medis. Hanya untuk dukungan informatif dan perawatan.
            </p>
          </div>

          <nav aria-label="Footer navigation" className="md:justify-self-center">
            <h2 className="text-xs font-semibold uppercase tracking-[0.18em] text-[#B8D5B8]">
              Jelajahi
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
        </div>

        <div className="mt-10 flex flex-col gap-3 border-t border-white/10 pt-6 text-xs text-white/40 sm:flex-row sm:items-center sm:justify-between">
          <p>&copy; 2026 TIARA Platform. Hak cipta dilindungi.</p>
          <p>Dibangun untuk perawatan yang penuh perhatian dan terhubung.</p>
        </div>
      </div>
    </footer>
  );
}
