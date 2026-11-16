import { type Configuration, LogLevel, PublicClientApplication } from '@azure/msal-browser';

const clientId = import.meta.env.VITE_AZURE_CLIENT_ID?.trim() ?? '';
const tenantId = import.meta.env.VITE_AZURE_TENANT_ID?.trim() || 'common';
const redirectUri = import.meta.env.VITE_AZURE_REDIRECT_URI?.trim() || window.location.origin;

export const azureConfigured = Boolean(clientId);

export const msalConfig: Configuration = {
  auth: {
    clientId: clientId || '00000000-0000-0000-0000-000000000000',
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri,
    postLogoutRedirectUri: redirectUri,
    navigateToLoginRequestUrl: false,
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      logLevel: LogLevel.Warning,
      loggerCallback: (_level, message, containsPii) => {
        if (!containsPii && import.meta.env.DEV) {
          console.debug('[msal]', message);
        }
      },
    },
  },
};

export const loginRequest = {
  scopes: ['User.Read', 'openid', 'profile', 'email'],
};

export const msalInstance = azureConfigured
  ? new PublicClientApplication(msalConfig)
  : null;

export const allowDevLogin = import.meta.env.VITE_ALLOW_DEV_LOGIN !== 'false';
