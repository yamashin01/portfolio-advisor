import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t py-6 text-center text-sm text-muted-foreground">
      <div className="mx-auto max-w-5xl px-4">
        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link href="/terms" className="hover:underline">
            利用規約
          </Link>
          <span aria-hidden="true">|</span>
          <Link href="/risk-disclosure" className="hover:underline">
            リスク開示
          </Link>
        </div>
        <p className="mt-2">
          本サービスは教育目的であり、投資助言ではありません。
        </p>
      </div>
    </footer>
  );
}
