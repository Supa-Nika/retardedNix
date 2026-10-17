{ config, pkgs, username, ... }:

let
  qemuFresh = import ../../pkgs/qemu-fresh.nix { inherit pkgs; }; 
in
{
  imports = [
    ./hardware-configuration.nix
    ../../modules/boot.nix
    ../../modules/nvidia.nix
    ../../modules/desktop.nix
    ../../modules/gaming.nix
    ../../modules/obs.nix
    ../../modules/networking.nix
    ../../modules/streamDeck.nix
    ../../modules/waydroid.nix
  ];

  time.timeZone = "Europe/Warsaw";
  i18n.defaultLocale = "en_US.UTF-8";

  users.users.${username} = {
    isNormalUser = true;
    description = username;
    extraGroups = [ "wheel" "networkmanager" "video" "audio" "input" "dialout" "uucp" "i2c" "render" "adbusers" "libvirtd" "kvm" ];
    shell = pkgs.bash;
  };

  environment.systemPackages = with pkgs; [
    fastfetch
    killall
    kitty
    wl-clipboard
    grim
    slurp
    swappy
    brightnessctl
    playerctl
    xdg-utils
    xwayland-satellite
    vscode
    nvitop
    htop
    protonup-qt
    audacity
    kdePackages.gwenview
    kdePackages.kolourpaint
    kdePackages.ark
    bazaar
    p7zip
    unrar
    zip
    unzip
    gzip
    bzip2
    xz
    zstd
    python314
    python314Packages.pip
    arduino-cli
    gcc
    clang
    cmake
    ninja
    gnumake
    pkg-config
    gdb
    clang-tools
    nirius
    yt-dlp
    ffmpeg
    git
    perl
    beammp-launcher
    zerotierone
    steam-run
    gamescope
    pavucontrol
    jdk25
    awww
    android-tools
    v4l-utils
    psmisc
    pulseaudio
    atuin
    ydotool
    ddcutil
    xwayland
    parted
    xorriso
    nodejs_26
    vulkan-tools
    mesa-demos
    qemuFresh # remember to update later when nixpkgs catches up
    piper
    rivalcfg
    kdePackages.kdeconnect-kde
    scrcpy
    # gnome-boxes
    
  ];

  # programs.virt-manager.enable = true;

  # virtualisation.spiceUSBRedirection.enable = true;
  # virtualisation.libvirtd = {
  #   enable = true;
  # };

  nixpkgs.config.permittedInsecurePackages = [
    "ventoy-1.1.12"
  ];

  services.flatpak.enable = true;
  services.streamdeck-handler.enable = true;

  programs.nix-ld = {
    enable = true;
    libraries = with pkgs; [
      stdenv.cc.cc
      zlib
      glibc
    ];
  };

  services.udev.packages = [ 
    pkgs.platformio-core
    pkgs.openocd
    pkgs.rivalcfg
  ];

  services.udev.extraRules = ''
    KERNEL=="ttyUSB[0-9]*", MODE="0666", GROUP="dialout"
    KERNEL=="ttyACM[0-9]*", MODE="0666", GROUP="dialout"
    
    SUBSYSTEM=="usb", ATTR{idVendor}=="1038", MODE="0666"
  '';

  services.udisks2.enable = true;

  nixpkgs.config.allowUnfree = true;
  nixpkgs.config.android_sdk.accept_license = true;

  services.pipewire = {
    enable = true;
    alsa.enable = true;
    alsa.support32Bit = true;
    pulse.enable = true;
  };


  xdg.portal = {
    enable = true;
    wlr.enable = true;
    extraPortals = [ 
      pkgs.xdg-desktop-portal-gnome
      pkgs.xdg-desktop-portal-gtk 
    ];
    config.common.default = "*";
  };

  services.ratbagd.enable = true;

  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  system.stateVersion = "26.05";
}