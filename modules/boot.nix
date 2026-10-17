{ config, pkgs, ... }:

{
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;
  boot.loader.systemd-boot.configurationLimit = 5;

  boot.initrd.kernelModules = [ 
    "nvidia" 
    "nvidia_modeset" 
    "nvidia_uvm" 
    "nvidia_drm" 
  ];

  boot.extraModulePackages = [
    config.boot.kernelPackages.v4l2loopback
  ];
  
  boot.kernelParams = [
    "nvidia_drm.modeset=1"
    "nvidia_drm.fbdev=1"
    "resume_offset=42432512"
  ];

  boot.kernelModules = [
    "v4l2loopback"
    "i2c-dev"
    "udmabuf"
  ];

  boot.extraModprobeConfig = ''
    options v4l2loopback devices=2 video_nr=10,11 card_label="DroidCam,OBS Virtual Camera" exclusive_caps=1,1
  '';

  boot.supportedFilesystems = [ "ntfs" "exfat" "btrfs" ];

  zramSwap = {
    enable = true;
    algorithm = "zstd";
    memoryPercent = 50;
    priority = 100;
  };
  
  swapDevices = [ {
    device = "/swapfile";
    size = 36 * 1024;
    priority = 1;
  } ];

  boot.resumeDevice = "/dev/disk/by-uuid/5a3bc9cb-cb7b-47d1-ad41-fd8d4e2bc6ac";
}