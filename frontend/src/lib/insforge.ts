import { createClient } from '@insforge/sdk';

// Insforge client configuration
// The base URL and anon key should match your Insforge project
const INSFORGE_BASE_URL = import.meta.env.VITE_INSFORGE_BASE_URL || 'http://localhost:7130';
const INSFORGE_ANON_KEY = import.meta.env.VITE_INSFORGE_ANON_KEY || '';

export const insforge = createClient({
  baseUrl: INSFORGE_BASE_URL,
  anonKey: INSFORGE_ANON_KEY,
});

export type User = {
  id: string;
  email: string;
  emailVerified: boolean;
  profile?: {
    name?: string;
    avatar_url?: string;
  };
  createdAt: string;
  updatedAt: string;
};
