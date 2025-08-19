import { User } from '../types';
import { apiService } from './api';

class AuthService {
  private currentUser: User | null = null;

  async login(username: string, password: string): Promise<User> {
    const token = await apiService.login({ username, password });
    const user = await apiService.getCurrentUser();
    this.currentUser = user;
    return user;
  }

  async register(userData: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }): Promise<void> {
    await apiService.register(userData);
  }

  async logout(): Promise<void> {
    await apiService.logout();
    this.currentUser = null;
  }

  async getCurrentUser(): Promise<User | null> {
    if (this.currentUser) {
      return this.currentUser;
    }

    const token = localStorage.getItem('auth_token');
    if (!token) {
      return null;
    }

    try {
      const user = await apiService.getCurrentUser();
      this.currentUser = user;
      return user;
    } catch (error) {
      console.error('Failed to get current user:', error);
      localStorage.removeItem('auth_token');
      return null;
    }
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth_token');
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }
}

export const authService = new AuthService();
