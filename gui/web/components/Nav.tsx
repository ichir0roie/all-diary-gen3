"use client";

import { signOut } from "aws-amplify/auth";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { loginRequired } from "@/lib/auth";
import { T } from "@/lib/text";

const LINKS = [
  { href: "/", label: T.nav.diary },
  { href: "/on-this-day", label: T.nav.onThisDay },
  { href: "/heatmap", label: T.nav.heatmap },
  { href: "/similar", label: T.nav.similar },
  { href: "/data", label: T.nav.data },
];

export default function Nav() {
  const pathname = usePathname();
  return (
    <nav className="nav">
      <Link href="/" className="brand">{T.appName}</Link>
      {LINKS.map((link) => (
        <Link key={link.href} href={link.href} className={pathname === link.href ? "active" : ""}>
          {link.label}
        </Link>
      ))}
      {loginRequired && (
        <button type="button" className="ghost sign-out" onClick={() => signOut()}>
          {T.nav.signOut}
        </button>
      )}
    </nav>
  );
}
