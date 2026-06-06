import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { SalesRepresentative } from "@/api/types";
import { clearSessionToken, getSessionToken, setSessionToken } from "@/auth/sessionStorage";

type AuthContextValue = {
  token: string | null;
  representative: SalesRepresentative | null;
  isAuthenticated: boolean;
  setSession: (token: string, representative: SalesRepresentative) => void;
  clearSession: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getSessionToken());
  const [representative, setRepresentative] = useState<SalesRepresentative | null>(null);

  const setSession = useCallback((newToken: string, rep: SalesRepresentative) => {
    setSessionToken(newToken);
    setToken(newToken);
    setRepresentative(rep);
  }, []);

  const clearSession = useCallback(() => {
    clearSessionToken();
    setToken(null);
    setRepresentative(null);
  }, []);

  const value = useMemo(
    () => ({
      token,
      representative,
      isAuthenticated: Boolean(token),
      setSession,
      clearSession,
    }),
    [token, representative, setSession, clearSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
