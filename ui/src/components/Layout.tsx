import { ReactNode } from "react";
import { Link } from "react-router-dom";
import { FileText } from "lucide-react";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
          <FileText className="w-6 h-6 text-blue-600" />
          <Link to="/" className="text-lg font-semibold tracking-tight">
            SLA Renegotiation
          </Link>
        </div>
      </header>
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6">
        {children}
      </main>
    </div>
  );
}
