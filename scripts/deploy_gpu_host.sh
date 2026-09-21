#!/usr/bin/env bash
# Launch a GPU host for the current platform version and reach it over an SSH
# tunnel. Nothing is published to the internet: the security group opens SSH to
# one address and no other port, because the platform's HTTP API has no
# authentication of its own (`POST /api/runs` validates its body, it does not
# check a caller), so a public port is a public right to spend the model budget.
#
# Creates only new resources, tagged Project=refactor-platform-gpu. It never
# reads or modifies an existing instance, volume, or security group.
#
#   AWS_PROFILE=pischool ./scripts/deploy_gpu_host.sh            # launch
#   AWS_PROFILE=pischool ./scripts/deploy_gpu_host.sh --dry-run  # verify only
#
# ponytail: no Terraform, no CloudFormation, no autoscaling. One instance that
# one person starts before a demo and stops after. Reach for IaC when a second
# person needs to reproduce it without reading this file.
set -euo pipefail

PROFILE="${AWS_PROFILE:-pischool}"
REGION="${AWS_REGION:-eu-north-1}"
SUBNET="${SUBNET:-subnet-08709e61}"          # eu-north-1a, same VPC as the July host
VPC="${VPC:-vpc-988169f1}"
TYPE="${TYPE:-g4dn.xlarge}"                  # T4 16 GB: the two models need 9.1 GB
DISK="${DISK:-150}"                          # images 8 GB + models 9 GB + workspaces
KEY="${KEY:-coderefactor}"
AMI="${AMI:-ami-00f388df5933725cb}"          # DL Base OSS Nvidia Driver, Ubuntu 22.04
NAME="${NAME:-refactor-platform-gpu}"
DRY=""; [ "${1:-}" = "--dry-run" ] && DRY="--dry-run"

aws() { command aws --profile "$PROFILE" --region "$REGION" "$@"; }

MYIP="$(curl -fsS https://checkip.amazonaws.com)/32"
echo "SSH will be opened to $MYIP only. No other ingress."

# A dry run must not create anything, so it validates against the VPC default
# group instead of making ours.
SG="$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$NAME-ssh" \
      "Name=vpc-id,Values=$VPC" --query 'SecurityGroups[0].GroupId' --output text)"
if [ "$SG" = "None" ] || [ -z "$SG" ]; then
  if [ -n "$DRY" ]; then
    SG="$(aws ec2 describe-security-groups --filters "Name=group-name,Values=default" \
          "Name=vpc-id,Values=$VPC" --query 'SecurityGroups[0].GroupId' --output text)"
    echo "dry run: validating against the VPC default group $SG"
  else
    SG="$(aws ec2 create-security-group --group-name "$NAME-ssh" --vpc-id "$VPC" \
          --description "SSH from one address; the platform is reached over a tunnel" \
          --query GroupId --output text)"
    aws ec2 authorize-security-group-ingress --group-id "$SG" \
      --protocol tcp --port 22 --cidr "$MYIP" >/dev/null
    echo "created security group $SG"
  fi
else
  echo "reusing security group $SG"
  # Reusing a group by name means inheriting whatever its rules are now. Refuse
  # if anything opened it to the world, rather than launching into it while
  # claiming above that only one address can reach it.
  WIDE="$(aws ec2 describe-security-groups --group-ids "$SG" \
          --query "SecurityGroups[].IpPermissions[].IpRanges[?CidrIp=='0.0.0.0/0'].CidrIp" \
          --output text)"
  if [ -n "$WIDE" ]; then
    echo "refusing: $SG already allows 0.0.0.0/0. Narrow it, or delete it and" >&2
    echo "re-run so this script recreates it with SSH from $MYIP only." >&2
    exit 1
  fi
  # The address changes with the network, so re-authorise it each launch.
  [ -n "$DRY" ] || aws ec2 authorize-security-group-ingress --group-id "$SG" \
    --protocol tcp --port 22 --cidr "$MYIP" >/dev/null 2>&1 || true
fi

# A dry run ends in DryRunOperation, which is the success signal, not a failure.
if [ -n "$DRY" ]; then
  # `aws` exits non-zero on DryRunOperation, and pipefail would read that as a
  # failure, so capture the output and match it instead of piping.
  OUT="$(aws ec2 run-instances --dry-run \
      --image-id "$AMI" --instance-type "$TYPE" --key-name "$KEY" \
      --subnet-id "$SUBNET" --security-group-ids "$SG" \
      --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":$DISK,\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]" \
      2>&1 || true)"
  if printf '%s' "$OUT" | grep -q DryRunOperation; then
    echo "dry run OK: $TYPE, ${DISK}GB gp3, $AMI in $SUBNET would launch. Nothing created."
    exit 0
  fi
  echo "dry run FAILED: the launch would be rejected" >&2
  exit 1
fi

ID="$(aws ec2 run-instances \
  --image-id "$AMI" --instance-type "$TYPE" --key-name "$KEY" \
  --subnet-id "$SUBNET" --security-group-ids "$SG" \
  --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":$DISK,\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME},{Key=Project,Value=refactor-platform-gpu},{Key=Owner,Value=aziz}]" \
  --query 'Instances[0].InstanceId' --output text)"

echo "launched $ID, waiting for it to run"
aws ec2 wait instance-running --instance-ids "$ID"
IP="$(aws ec2 describe-instances --instance-ids "$ID" \
      --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)"

cat <<EOF

  instance $ID at $IP (\$0.58/hr compute: stop it when you are not demoing)

  1. ssh -i ~/.ssh/$KEY.pem ubuntu@$IP
  2. git clone https://github.com/PiSchool/refactor-platform && cd refactor-platform
     cp .env.example .env && \$EDITOR .env        # OPENROUTER_API_KEY, DB passwords
     docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d
     docker compose exec backend python -m app.catalog.bootstrap
  3. From your laptop, tunnel instead of exposing a port:
       ssh -i ~/.ssh/$KEY.pem -L 8787:localhost:8787 ubuntu@$IP
     then open http://localhost:8787

  stop:      aws ec2 stop-instances --profile $PROFILE --instance-ids $ID
  terminate: aws ec2 terminate-instances --profile $PROFILE --instance-ids $ID
EOF
