import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { insforge, User, UserRole } from "../lib/insforge";

// Session storage keys
const SESSION_KEY = "mediguardai_session";

interface StoredSession {
  accessToken: string;
  user: User;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signUp: (email: string, password: string, name: string, role: UserRole) => Promise<{ error: Error | null; requireVerification?: boolean }>;
  signOut: () => Promise<void>;
  isDoctor: boolean;
  isPatient: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper functions for session persistence
function saveSession(accessToken: string, user: User) {
  try {
    const session: StoredSession = { accessToken, user };
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } catch (err) {
    console.error("Failed to save session:", err);
  }
}

function loadSession(): StoredSession | null {
  try {
    const stored = localStorage.getItem(SESSION_KEY);
    if (stored) {
      return JSON.parse(stored) as StoredSession;
    }
  } catch (err) {
    console.error("Failed to load session:", err);
  }
  return null;
}

function clearSession() {
  try {
    localStorage.removeItem(SESSION_KEY);
  } catch (err) {
    console.error("Failed to clear session:", err);
  }
}

// Fetch profile from database
async function fetchProfileFromDB(userId: string): Promise<{ name?: string; role?: UserRole } | null> {
  try {
    const { data, error } = await insforge.database
      .from("profiles")
      .select("name, role")
      .eq("user_id", userId)
      .maybeSingle();

    if (error || !data) {
      return null;
    }

    return {
      name: data.name as string | undefined,
      role: data.role as UserRole | undefined,
    };
  } catch (err) {
    console.error("Failed to fetch profile from DB:", err);
    return null;
  }
}

// Create or update profile in database
async function upsertProfileInDB(userId: string, name: string, role: UserRole): Promise<boolean> {
  try {
    // First try to update
    const { data: existingProfile } = await insforge.database
      .from("profiles")
      .select("id")
      .eq("user_id", userId)
      .maybeSingle();

    if (existingProfile) {
      // Update existing profile
      const { error } = await insforge.database
        .from("profiles")
        .update({ name, role, updated_at: new Date().toISOString() })
        .eq("user_id", userId);

      return !error;
    } else {
      // Insert new profile
      const { error } = await insforge.database
        .from("profiles")
        .insert({ user_id: userId, name, role });

      return !error;
    }
  } catch (err) {
    console.error("Failed to upsert profile in DB:", err);
    return false;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    const checkUser = async () => {
      try {
        // First, try to restore from localStorage
        const storedSession = loadSession();
        if (storedSession?.user) {
          setUser(storedSession.user);
          setLoading(false);

          // Verify session is still valid in background
          try {
            const { data, error } = await insforge.auth.getCurrentUser();
            if (error || !data?.user) {
              // Session expired, clear it
              clearSession();
              setUser(null);
            } else {
              // Refresh profile data from database
              const profile = await fetchProfileFromDB(data.user.id);
              const userWithProfile = {
                ...data.user,
                profile: {
                  ...data.user.profile,
                  name: profile?.name || data.user.profile?.name,
                  role: profile?.role,
                },
              } as User;
              setUser(userWithProfile);
              // Update stored session with fresh data
              if (storedSession.accessToken) {
                saveSession(storedSession.accessToken, userWithProfile);
              }
            }
          } catch (err) {
            // Network error, keep using stored session
            console.warn("Could not verify session:", err);
          }
          return;
        }

        // No stored session, try SDK's getCurrentUser
        const { data, error } = await insforge.auth.getCurrentUser();
        if (data?.user && !error) {
          // Fetch profile from database
          const profile = await fetchProfileFromDB(data.user.id);
          const userWithProfile = {
            ...data.user,
            profile: {
              ...data.user.profile,
              name: profile?.name || data.user.profile?.name,
              role: profile?.role,
            },
          } as User;
          setUser(userWithProfile);
        }
      } catch (err) {
        console.error("Failed to get current user:", err);
      } finally {
        setLoading(false);
      }
    };

    checkUser();
  }, []);

  const signIn = async (email: string, password: string) => {
    try {
      const { data, error } = await insforge.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        return { error };
      }

      if (data?.user) {
        // Fetch profile from database
        const profile = await fetchProfileFromDB(data.user.id);
        const userWithProfile = {
          ...data.user,
          profile: {
            ...data.user.profile,
            name: profile?.name || data.user.profile?.name,
            role: profile?.role,
          },
        } as User;

        setUser(userWithProfile);

        // Save session to localStorage for persistence
        if (data.accessToken) {
          saveSession(data.accessToken, userWithProfile);
        }
      }

      return { error: null };
    } catch (err) {
      return { error: err as Error };
    }
  };

  const signUp = async (email: string, password: string, name: string, role: UserRole) => {
    try {
      const { data, error } = await insforge.auth.signUp({
        email,
        password,
        name,
      });

      if (error) {
        return { error };
      }

      if (data?.requireEmailVerification) {
        return { error: null, requireVerification: true };
      }

      if (data?.user && data?.accessToken) {
        // Store profile in database
        const profileSaved = await upsertProfileInDB(data.user.id, name, role);
        if (!profileSaved) {
          console.error("Failed to save profile to database");
        }

        const userWithRole = {
          ...data.user,
          profile: {
            ...data.user.profile,
            name,
            role,
          },
        } as User;

        setUser(userWithRole);

        // Save session to localStorage for persistence
        saveSession(data.accessToken, userWithRole);
      }

      return { error: null };
    } catch (err) {
      return { error: err as Error };
    }
  };

  const signOut = async () => {
    try {
      await insforge.auth.signOut();
    } catch (err) {
      console.error("Failed to sign out from server:", err);
    } finally {
      // Always clear local state and storage
      setUser(null);
      clearSession();
    }
  };

  const isDoctor = user?.profile?.role === "doctor";
  const isPatient = user?.profile?.role === "patient";

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut, isDoctor, isPatient }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
