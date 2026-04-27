"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import webConfig from "@/constants/common-env";
import { clearStoredAuthSession, getStoredAuthSession, type StoredAuthSession } from "@/store/auth";
import { cn } from "@/lib/utils";

const adminNavItems = [
  { href: "/image", label: "画图" },
  { href: "/accounts", label: "号池管理" },
  { href: "/image-manager", label: "图片管理" },
  { href: "/logs", label: "日志管理" },
  { href: "/settings", label: "设置" },
];

const userNavItems = [{ href: "/image", label: "画图" }];

function Image2ApiLogo() {
  return (
    <span className="relative inline-flex size-8 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-stone-950 shadow-sm shadow-stone-950/15 ring-1 ring-stone-900/10 transition group-hover:shadow-md group-hover:shadow-indigo-500/20">
      <svg className="size-8" viewBox="0 0 32 32" role="img" aria-hidden="true" focusable="false">
        <defs>
          <linearGradient id="image2api-logo-bg" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
            <stop stopColor="#111827" />
            <stop offset="0.48" stopColor="#4f46e5" />
            <stop offset="1" stopColor="#06b6d4" />
          </linearGradient>
          <linearGradient id="image2api-logo-glow" x1="9" y1="8" x2="24" y2="25" gradientUnits="userSpaceOnUse">
            <stop stopColor="#ffffff" stopOpacity="0.95" />
            <stop offset="1" stopColor="#cffafe" stopOpacity="0.78" />
          </linearGradient>
        </defs>
        <rect width="32" height="32" rx="10" fill="url(#image2api-logo-bg)" />
        <path d="M7.8 20.4 12 16.1l3.1 3.2 2.7-2.8 6.4 6.8H8.6a2 2 0 0 1-1.4-.6 1.6 1.6 0 0 1 .6-2.3Z" fill="url(#image2api-logo-glow)" opacity="0.92" />
        <path d="M8.5 9.5h11a3 3 0 0 1 3 3v7.8" fill="none" stroke="#fff" strokeOpacity="0.86" strokeWidth="1.7" strokeLinecap="round" />
        <path d="M22.8 12.2h1.9c1.6 0 2.8 1.2 2.8 2.8s-1.2 2.8-2.8 2.8h-1.9" fill="none" stroke="#a5f3fc" strokeWidth="1.7" strokeLinecap="round" />
        <path d="M20.6 15h5.3" stroke="#fff" strokeWidth="1.7" strokeLinecap="round" />
        <circle cx="11" cy="12" r="2.1" fill="#fef3c7" />
        <circle cx="25.8" cy="15" r="1.25" fill="#fff" />
        <path d="M18.8 24.5h5.8m-2.9-2.9 2.9 2.9-2.9 2.9" fill="none" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className="pointer-events-none absolute inset-0 rounded-2xl bg-white/0 ring-1 ring-inset ring-white/25" />
    </span>
  );
}


export function TopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [session, setSession] = useState<StoredAuthSession | null | undefined>(undefined);

  useEffect(() => {
    let active = true;

    const load = async () => {
      if (pathname === "/login") {
        if (!active) {
          return;
        }
        setSession(null);
        return;
      }

      const storedSession = await getStoredAuthSession();
      if (!active) {
        return;
      }
      setSession(storedSession);
    };

    void load();
    return () => {
      active = false;
    };
  }, [pathname]);

  const handleLogout = async () => {
    await clearStoredAuthSession();
    router.replace("/login");
  };

  if (pathname === "/login" || session === undefined || !session) {
    return null;
  }

  const navItems = session.role === "admin" ? adminNavItems : userNavItems;
  const roleLabel = session.role === "admin" ? "管理员" : "普通用户";

  return (
    <header className="border-b border-stone-100/50">
      <div className="flex h-12 items-center justify-between px-3 sm:px-6">
        <div className="flex items-center gap-2 sm:gap-3">
          <Link
            href="/image"
            className="group inline-flex items-center gap-2 rounded-2xl py-1 pr-2 transition hover:-translate-y-px"
            aria-label="image2api 首页"
          >
            <Image2ApiLogo />
            <span className="bg-gradient-to-r from-stone-950 via-indigo-700 to-cyan-600 bg-clip-text text-[15px] font-black tracking-tight text-transparent sm:text-base">
              image2api
            </span>
          </Link>
        </div>
        <div className="flex flex-1 justify-center gap-3 sm:gap-8">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative py-1 text-[13px] font-medium transition sm:text-[15px]",
                  active ? "font-semibold text-stone-950" : "text-stone-500 hover:text-stone-900",
                )}
              >
                {item.label}
                {active ? <span className="absolute inset-x-0 -bottom-[1px] h-0.5 bg-stone-950" /> : null}
              </Link>
            );
          })}
        </div>
        <div className="flex items-center justify-end gap-2 sm:gap-3">
          <span className="hidden rounded-md bg-stone-100 px-2 py-1 text-[10px] font-medium text-stone-500 sm:inline-block sm:text-[11px]">
            {roleLabel}
          </span>
          <span className="hidden rounded-md bg-stone-100 px-2 py-1 text-[10px] font-medium text-stone-500 sm:inline-block sm:text-[11px]">
            v{webConfig.appVersion}
          </span>
          <button
            type="button"
            className="py-1 text-xs text-stone-400 transition hover:text-stone-700 sm:text-sm"
            onClick={() => void handleLogout()}
          >
            退出
          </button>
        </div>
      </div>
    </header>
  );
}
