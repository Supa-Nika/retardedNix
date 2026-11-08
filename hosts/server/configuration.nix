{ config, pkgs, lib, username, ... }:

{
  imports = [
    ./hardware-configuration.nix

    # shared by every machine
    ../../modules/common/base.nix
    ../../modules/common/packages.nix
    ../../modules/common/zerotier.nix
  ];

  # Legacy BIOS boot (no /boot partition, no NVMe on this machine)
  boot.loader.grub.enable = true;
  boot.loader.grub.device = "/dev/sda";
  boot.loader.grub.useOSProber = true;

  networking.useDHCP = false;
  networking.networkmanager = {
    enable = true;
    ensureProfiles = {
      environmentFiles = [ "/etc/wifi.env" ];
      profiles.home-wifi = {
        connection = {
          id = "home-wifi";
          type = "wifi";
        };
        wifi = {
          ssid = "$WIFI_SSID";
          mode = "infrastructure";
        };
        wifi-security = {
          key-mgmt = "wpa-psk";
          psk = "$WIFI_PSK";
        };
        ipv4 = {
          method = "manual";
          address1 = "192.168.1.68/24,192.168.1.1";
          dns = "192.168.1.1;1.1.1.1;";
        };
        ipv6.method = "auto";
      };
    };
  };

  networking.firewall = {
    enable = true;
    allowPing = true;                 # this is already the default
    allowedTCPPorts = [ 22 ];         # SSH, add other ports your bot or services need
  };

  # Polish locale details / keymap
  i18n.extraLocaleSettings = {
    LC_ADDRESS = "pl_PL.UTF-8";
    LC_IDENTIFICATION = "pl_PL.UTF-8";
    LC_MEASUREMENT = "pl_PL.UTF-8";
    LC_MONETARY = "pl_PL.UTF-8";
    LC_NAME = "pl_PL.UTF-8";
    LC_NUMERIC = "pl_PL.UTF-8";
    LC_PAPER = "pl_PL.UTF-8";
    LC_TELEPHONE = "pl_PL.UTF-8";
    LC_TIME = "pl_PL.UTF-8";
  };

  services.xserver.xkb = {
    layout = "pl";
    variant = "";
  };
  console.keyMap = "pl2";

  users.users.${username} = {
    isNormalUser = true;
    description = username;
    extraGroups = [ "wheel" "networkmanager" ];
  };

  services.openssh.enable = true;

  services.tardbot = {
    enable = true; #[cite: 5]
    environmentFile = "/etc/tardbot.env"; # Path to file containing DISCORD_TOKEN=...[cite: 5]
    modules = [ "music" "general" "r34" "vcmanager" ];     # Optional: specific modules to load[cite: 5]
    
    # Optional extra settings / environment variables
    settings = {
      INTERLEAVE_MODE = "spread";
      YTDLP_CLIENTS = "visionos";
      TEMP_VC_CATEGORY_ID = "1454932444825260262";
      VC_COMMAND_COOLDOWN = "10";
    };
  };

  system.stateVersion = "26.05";
}
