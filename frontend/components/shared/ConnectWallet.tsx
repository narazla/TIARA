"use client";

import { useState, useEffect } from "react";
import { Wallet, CheckCircle2, AlertCircle } from "lucide-react";

interface EthereumProvider {
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
  on?: (event: string, listener: (...args: unknown[]) => void) => void;
  removeListener?: (event: string, listener: (...args: unknown[]) => void) => void;
}

interface EthereumError {
  code?: number;
  message?: string;
}

declare global {
  interface Window {
    ethereum?: EthereumProvider;
  }
}

// BOT Chain Mainnet Configuration
const BOT_CHAIN_PARAMS = {
  chainId: "0x2A5", // 677 dalam hex
  chainName: "BOT Chain Mainnet",
  nativeCurrency: {
    name: "BOT",
    symbol: "BOT",
    decimals: 18,
  },
  rpcUrls: ["https://rpc.botchain.ai"],
  blockExplorerUrls: ["https://scan.bohr.life"],
};

export function ConnectWallet() {
  const [account, setAccount] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  async function checkConnection(provider: EthereumProvider) {
    try {
      const accounts = (await provider.request({ method: "eth_accounts" })) as string[];
      setAccount(accounts[0] || null);
    } catch (err) {
      console.error("Error checking wallet connection:", err);
    }
  }

  useEffect(() => {
    const provider = window.ethereum;
    if (!provider) return;

    const handleAccountsChanged = (...args: unknown[]) => {
      const accounts = (args[0] as string[] | undefined) || [];
      setAccount(accounts[0] || null);
    };

    const connectionCheck = window.setTimeout(() => {
      void checkConnection(provider);
    }, 0);
    provider.on?.("accountsChanged", handleAccountsChanged);

    return () => {
      window.clearTimeout(connectionCheck);
      provider.removeListener?.("accountsChanged", handleAccountsChanged);
    };
  }, []);

  const connectWallet = async () => {
    if (isConnecting) return;
    setError(null);
    const provider = typeof window !== "undefined" ? window.ethereum : undefined;
    if (!provider) {
      setError("MetaMask not detected! Please install MetaMask.");
      if (typeof window !== "undefined") {
        window.open("https://metamask.io/download/", "_blank");
      }
      return;
    }

    setIsConnecting(true);
    try {
      const accounts = (await provider.request({
        method: "eth_requestAccounts",
      })) as string[];
      setAccount(accounts[0] || null);

      try {
        await provider.request({
          method: "wallet_switchEthereumChain",
          params: [{ chainId: BOT_CHAIN_PARAMS.chainId }],
        });
      } catch (switchError) {
        const error = switchError as EthereumError;
        if (error.code === 4902) {
          await provider.request({
              method: "wallet_addEthereumChain",
              params: [BOT_CHAIN_PARAMS],
          });
        } else {
          throw switchError;
        }
      }
    } catch (err) {
      const error = err as EthereumError;
      const isRequestPending =
        error.code === -32002 || error.message?.toLowerCase().includes("already pending");
      setError(
        isRequestPending
          ? "A wallet request is already open. Approve or reject it in MetaMask, then try again."
          : error.message || "Failed to connect wallet"
      );
    } finally {
      setIsConnecting(false);
    }
  };

  const formatAddress = (addr: string) => {
    return `${addr.substring(0, 6)}...${addr.substring(addr.length - 4)}`;
  };

  return (
    <div className="flex flex-col items-end">
      {account ? (
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 px-4 py-2 rounded-xl text-emerald-600 text-sm font-medium">
          <CheckCircle2 className="w-4 h-4" />
          <span>{formatAddress(account)}</span>
        </div>
      ) : (
        <button
          onClick={connectWallet}
          disabled={isConnecting}
          className="flex items-center gap-2 bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-xl text-sm font-medium transition-all shadow-sm"
        >
          <Wallet className="w-4 h-4" />
          <span>{isConnecting ? "Connecting..." : "Connect Wallet"}</span>
        </button>
      )}
      {error && (
        <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" /> {error}
        </p>
      )}
    </div>
  );
}