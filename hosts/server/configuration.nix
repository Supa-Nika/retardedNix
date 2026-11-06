{ config, pkgs, username, ... }:

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

  # ---------------------------------------------------------------------
  # Networking: static 192.168.1.68.
  # systemd-networkd matches any wired "en*" interface, so the exact
  # interface name doesn't have to be known/hardcoded.
  # ---------------------------------------------------------------------
  networking.useDHCP = false;
  networking.networkmanager.enable = false;
  systemd.network.enable = true;
  systemd.network.networks."10-lan" = {
    matchConfig.Name = "en*";
    address = [ "192.168.1.68/24" ];
    gateway = [ "192.168.1.254" ];
    dns = [ "1.1.1.1" "8.8.8.8" ];
    networkConfig.DHCP = "no";
    linkConfig.RequiredForOnline = "routable";
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
    extraGroups = [ "wheel" ];
  };

  services.openssh.enable = true;

  system.stateVersion = "26.05";
}
