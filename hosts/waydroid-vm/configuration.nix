{ pkgs, ... }:
let
  qemuFresh = import ../../pkgs/qemu-fresh.nix { inherit pkgs; };

  # Same QEMU, but qemu-kvm passes -accel (with honor-guest-pat) instead of
  # nixpkgs' default "-machine accel=kvm:tcg", which conflicts with -accel.
  qemuHonorPat = pkgs.symlinkJoin {
    name = "qemu-honor-pat";
    paths = [ qemuFresh ];
    postBuild = ''
      rm -f $out/bin/qemu-kvm
      cat > $out/bin/qemu-kvm <<'EOF'
      #!/bin/sh
      exec ${qemuFresh}/bin/qemu-system-x86_64 -accel kvm,honor-guest-pat=on "$@"
      EOF
      chmod +x $out/bin/qemu-kvm
    '';
  };
in
{

  hardware.graphics.enable = true;
  virtualisation.waydroid.enable = true;
  networking.firewall.trustedInterfaces = [ "waydroid0" ];

  programs.sway.enable = true;

  environment.etc."sway/config.d/vm.conf".text = ''
    bindsym Mod1+Return exec foot
    exec foot
  '';

  programs.bash.loginShellInit = ''
    if [ "$(tty)" = /dev/tty1 ]; then sway; fi
  '';

  environment.sessionVariables.WLR_NO_HARDWARE_CURSORS = "1";
  environment.systemPackages = with pkgs; [ vulkan-tools mesa-demos htop foot ];

  users.users.user = {
    isNormalUser = true;
    extraGroups = [ "wheel" "video" "render" ];
    initialPassword = "user";
  };
  security.sudo.wheelNeedsPassword = false;
  services.getty.autologinUser = "user";
  system.stateVersion = "26.05";

  networking.nftables.enable = true;
  boot.kernel.sysctl."net.ipv4.ip_forward" = 1;

  virtualisation.vmVariant.virtualisation = {
    memorySize = 8192;
    cores = 8;
    diskSize = 20480;
    qemu.package = qemuHonorPat;
    qemu.options = [
      "-vga none"
      "-device virtio-vga-gl,hostmem=4G,blob=true,venus=true"
      "-object memory-backend-memfd,id=mem1,size=8G"
      "-machine memory-backend=mem1"
      "-display gtk,gl=on"
    ];
    sharedDirectories = {
      waydroidApps = {
        source = "/home/mieciu/waydroid-shared";
        target = "/mnt/shared";
      };
    };
  };
}