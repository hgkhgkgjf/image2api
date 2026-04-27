"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { LoaderCircle, LockKeyhole, UserRound } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { login, loginWithPassword } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useRedirectIfAuthenticated } from "@/lib/use-auth-guard";
import { getDefaultRouteForRole, setStoredAuthSession } from "@/store/auth";

type LoginMode = "account" | "key";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<LoginMode>("account");
  const [authKey, setAuthKey] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { isCheckingAuth } = useRedirectIfAuthenticated();

  const finishLogin = async (data: Awaited<ReturnType<typeof login>>, key: string) => {
    await setStoredAuthSession({
      key,
      role: data.role,
      subjectId: data.subject_id,
      name: data.name,
    });
    router.replace(getDefaultRouteForRole(data.role));
  };

  const handleLogin = async () => {
    setIsSubmitting(true);
    try {
      if (mode === "account") {
        const normalizedUsername = username.trim();
        if (!normalizedUsername || !password) {
          toast.error("请输入用户名和密码");
          return;
        }
        const data = await loginWithPassword(normalizedUsername, password);
        if (!data.key) {
          throw new Error("登录未返回会话令牌");
        }
        await finishLogin(data, data.key);
      } else {
        const normalizedAuthKey = authKey.trim();
        if (!normalizedAuthKey) {
          toast.error("请输入密钥");
          return;
        }
        const data = await login(normalizedAuthKey);
        await finishLogin(data, normalizedAuthKey);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "登录失败";
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isCheckingAuth) {
    return (
      <div className="grid min-h-[calc(100vh-1rem)] w-full place-items-center px-4 py-6">
        <LoaderCircle className="size-5 animate-spin text-stone-400" />
      </div>
    );
  }

  return (
    <div className="grid min-h-[calc(100vh-1rem)] w-full place-items-center px-4 py-6">
      <Card className="w-full max-w-[505px] rounded-[30px] border-white/80 bg-white/95 shadow-[0_28px_90px_rgba(28,25,23,0.10)]">
        <CardContent className="space-y-7 p-6 sm:p-8">
          <div className="space-y-4 text-center">
            <div className="mx-auto inline-flex size-14 items-center justify-center rounded-[18px] bg-stone-950 text-white shadow-sm">
              {mode === "account" ? <UserRound className="size-5" /> : <LockKeyhole className="size-5" />}
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight text-stone-950">欢迎回来</h1>
              <p className="text-sm leading-6 text-stone-500">注册用户可用账号密码登录，管理员也可以继续用管理密钥登录。</p>
            </div>
          </div>

          <div className="grid grid-cols-2 rounded-2xl bg-stone-100 p-1 text-sm font-medium text-stone-600">
            <button
              type="button"
              className={cn("rounded-xl px-3 py-2 transition", mode === "account" && "bg-white text-stone-950 shadow-sm")}
              onClick={() => setMode("account")}
            >
              账号登录
            </button>
            <button
              type="button"
              className={cn("rounded-xl px-3 py-2 transition", mode === "key" && "bg-white text-stone-950 shadow-sm")}
              onClick={() => setMode("key")}
            >
              密钥登录
            </button>
          </div>

          {mode === "account" ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="username" className="block text-sm font-medium text-stone-700">用户名</label>
                <Input
                  id="username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void handleLogin();
                  }}
                  placeholder="请输入用户名"
                  className="h-13 rounded-2xl border-stone-200 bg-white px-4"
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-medium text-stone-700">密码</label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void handleLogin();
                  }}
                  placeholder="请输入密码"
                  className="h-13 rounded-2xl border-stone-200 bg-white px-4"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <label htmlFor="auth-key" className="block text-sm font-medium text-stone-700">密钥</label>
              <Input
                id="auth-key"
                type="password"
                value={authKey}
                onChange={(event) => setAuthKey(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") void handleLogin();
                }}
                placeholder="请输入管理员密钥或用户 API Key"
                className="h-13 rounded-2xl border-stone-200 bg-white px-4"
              />
            </div>
          )}

          <Button
            className="h-13 w-full rounded-2xl bg-stone-950 text-white hover:bg-stone-800"
            onClick={() => void handleLogin()}
            disabled={isSubmitting}
          >
            {isSubmitting ? <LoaderCircle className="size-4 animate-spin" /> : null}
            登录
          </Button>

          <div className="text-center text-sm text-stone-500">
            还没有账号？
            <Link href="/register" className="font-semibold text-stone-950 underline underline-offset-4">
              立即注册
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
