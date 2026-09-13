/**
 * Hardware detection service for Sovereign AI Workbench.
 * Safely determines whether NVIDIA GPU is available via nvidia-smi.
 * Missing GPU will NEVER crash or throw.
 */

const { execFile } = require("child_process");

let cachedHardwareInfo = null;

/**
 * Detect available hardware on the host.
 * @returns {Promise<{ nvidiaAvailable: boolean, mode: 'gpu'|'cpu', gpuName?: string, driverVersion?: string, detail: string }>}
 */
async function detectHardware() {
  if (cachedHardwareInfo !== null) {
    return cachedHardwareInfo;
  }

  const fallback = {
    nvidiaAvailable: false,
    mode: "cpu",
    gpuName: null,
    driverVersion: null,
    totalMemory: null,
    detail: "Using CPU / integrated graphics",
  };

  return new Promise((resolve) => {
    try {
      execFile(
        "nvidia-smi",
        ["--query-gpu=name,driver_version,memory.total", "--format=csv,noheader,nounits"],
        { timeout: 2500, windowsHide: true },
        (error, stdout) => {
          if (error || !stdout || !stdout.trim()) {
            console.log("ℹ️ Hardware: NVIDIA GPU not available -> CPU / integrated graphics mode enabled");
            cachedHardwareInfo = fallback;
            return resolve(fallback);
          }

          try {
            const parts = stdout.trim().split("\n")[0].split(",").map((s) => s.trim());
            const gpuName = parts[0] || "NVIDIA GPU";
            const driverVersion = parts[1] || "Unknown";
            const totalMemory = parts[2] ? `${parts[2]} MB` : "Unknown";

            console.log(`✅ Hardware: NVIDIA GPU detected -> ${gpuName} (Driver: ${driverVersion}, VRAM: ${totalMemory})`);
            console.log("ℹ️ GPU acceleration enabled for local Ollama");

            cachedHardwareInfo = {
              nvidiaAvailable: true,
              mode: "gpu",
              gpuName,
              driverVersion,
              totalMemory,
              detail: `${gpuName} (${totalMemory})`,
            };
            return resolve(cachedHardwareInfo);
          } catch (parseErr) {
            cachedHardwareInfo = fallback;
            return resolve(fallback);
          }
        }
      );
    } catch (err) {
      console.log("ℹ️ Hardware: NVIDIA GPU check skipped -> CPU mode enabled");
      cachedHardwareInfo = fallback;
      return resolve(fallback);
    }
  });
}

module.exports = {
  detectHardware,
};
