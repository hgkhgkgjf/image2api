"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { LoaderCircle, Sparkles, UserPlus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { registerUser } from "@/lib/api";
import { useRedirectIfAuthenticated } from "@/lib/use-auth-guard";
import { getDefaultRouteForRole, setStoredAuthSession } from "@/store/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { isCheckingAuth } = useRedirectIfAuthenticated();
  const [username, setUsername] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRegister = async () => {
    const normalizedUsername = username.trim();
    if (!normalizedUsername) {
      toast.error("请输入用户名");
      return;
    }
    if (password.length < 6) {
      toast.error("密码至少需要 6 位");
      return;
    }
    if (password !== confirmPassword) {
      toast.error("两次输入的密码不一致");
      return;
    }

    setIsSubmitting(true);
    try {
      const data = await registerUser({ username: normalizedUsername, password, name: name.trim() });
      if (!data.key) {
        throw new Error("注册未返回会话令牌");
      }
      await setStoredAuthSession({
        key: data.key,
        role: data.role,
        subjectId: data.subject_id,
        name: data.name,
      });
      toast.success("注册成功，已进入画图页面");
      router.replace(getDefaultRouteForRole(data.role));
    } catch (error) {
      const message = error instanceof Error ? error.message : "注册失败";
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
      <Card className="w-full max-w-[560px] rounded-[34px] border-white/80 bg-white/95 shadow-[0_28px_90px_rgba(28,25,23,0.10)]">
        <CardContent className="space-y-7 p-6 sm:p-8">
          <div className="space-y-4 text-center">
            <div className="mx-auto inline-flex size-14 items-center justify-center rounded-[20px] bg-gradient-to-br from-stone-950 via-indigo-700 to-cyan-500 text-white shadow-sm">
              <UserPlus className="size-5" />
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight text-stone-950">注册 image2api</h1>
              <p className="text-sm leading-6 text-stone-500">注册后可直接进入画图页面，历史记录会按你的账号单独保存。</p>
            </div>
          </div>

          <div className="rounded-2xl border border-sky-100 bg-sky-50 px-4 py-3 text-sm leading-6 text-sky-800">
            <div className="flex items-start gap-2">
              <Sparkles className="mt-0.5 size-4 shrink-0" />
              <span>新账号初始余额为 0 点，需要管理员在后台给你充值后才能生成图片。</span>
            </div>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="reg-username" className="block text-sm font-medium text-stone-700">用户名</label>
              <Input
                id="reg-username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="3-40 位，可用字母、数字、_、-、.、@"
                className="h-13 rounded-2xl border-stone-200 bg-white px-4"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="reg-name" className="block text-sm font-medium text-stone-700">显示名称（可选）</label>
              <Input
                id="reg-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="例如：张三 / 设计师 A"
                className="h-13 rounded-2xl border-stone-200 bg-white px-4"
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label htmlFor="reg-password" className="block text-sm font-medium text-stone-700">密码</label>
                <Input
                  id="reg-password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="至少 6 位"
                  className="h-13 rounded-2xl border-stone-200 bg-white px-4"
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="reg-confirm" className="block text-sm font-medium text-stone-700">确认密码</label>
                <Input
                  id="reg-confirm"
                  type="password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void handleRegister();
                  }}
                  placeholder="再次输入密码"
                  className="h-13 rounded-2xl border-stone-200 bg-white px-4"
                />
              </div>
            </div>
          </div>

          <Button
            className="h-13 w-full rounded-2xl bg-stone-950 text-white hover:bg-stone-800"
            onClick={() => void handleRegister()}
            disabled={isSubmitting}
          >
            {isSubmitting ? <LoaderCircle className="size-4 animate-spin" /> : null}
            注册并进入画图
          </Button>

          <div className="text-center text-sm text-stone-500">
            已有账号？
            <Link href="/login" className="font-semibold text-stone-950 underline underline-offset-4">
              返回登录
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
