import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import {
  getCurrentUser,
  login as loginRequest,
} from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(
    () => localStorage.getItem("access_token"),
  );

  const [refreshToken, setRefreshToken] = useState(
    () => localStorage.getItem("refresh_token"),
  );

  const [user, setUser] = useState(null);

  const [isLoadingUser, setIsLoadingUser] = useState(
    Boolean(accessToken),
  );

  const login = async (email, password) => {
    const data = await loginRequest(email, password);

    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);

    setAccessToken(data.access);
    setRefreshToken(data.refresh);

    const currentUser = await getCurrentUser();

    setUser(currentUser);

    return {
      ...data,
      user: currentUser,
    };
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    setIsLoadingUser(false);
  };

  useEffect(() => {
    const loadCurrentUser = async () => {
      if (!accessToken) {
        setIsLoadingUser(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();

        setUser(currentUser);
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        setAccessToken(null);
        setRefreshToken(null);
        setUser(null);
      } finally {
        setIsLoadingUser(false);
      }
    };

    loadCurrentUser();
  }, [accessToken]);

  const isAuthenticated = Boolean(accessToken && user);

  return (
    <AuthContext.Provider
      value={{
        accessToken,
        refreshToken,
        user,
        isAuthenticated,
        isLoadingUser,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside an AuthProvider.",
    );
  }

  return context;
}