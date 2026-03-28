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
const USER_KEY = "mediguardai_user";

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
    localStorage.removeItem(USER_KEY);
  } catch (err) {
    console.error("Failed to clear session:", err);
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
              // Refresh profile data
              const { data: profileData } = await insforge.auth.getProfile(data.user.id);
              const role = (profileData as Record<string, unknown>)?.role as UserRole | undefined;
              const userWithProfile = {
                ...data.user,
                profile: {
                  ...data.user.profile,
                  role,
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
          // Fetch full profile to get role
          const { data: profileData } = await insforge.auth.getProfile(data.user.id);
          const role = (profileData as Record<string, unknown>)?.role as UserRole | undefined;
          const userWithProfile = {
            ...data.user,
            profile: {
              ...data.user.profile,
              role,
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
        // Fetch full profile to get role
        const { data: profileData } = await insforge.auth.getProfile(data.user.id);
        const role = (profileData as Record<string, unknown>)?.role as UserRole | undefined;
        const userWithProfile = {
          ...data.user,
          profile: {
            ...data.user.profile,
            role,
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
        // Set the user's role in their profile
        await insforge.auth.setProfile({
          name,
          role,
        });

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

  const isDoctor = user?.profile?.role === 'doctor';
  const isPatient = user?.profile?.role === 'patient';

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
