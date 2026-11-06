{ ... }:
{
  fileSystems."/nix" = {
    device = "/dev/disk/by-uuid/82072618-0ec6-4f0a-b53c-48feb5b337ed";
    fsType = "btrfs";
    options = [ "subvol=nix" "noatime" ];
    neededForBoot = true;
  };
}