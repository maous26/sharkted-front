import { HTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "error" | "info";
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
          {
            "bg-gray-100 text-gray-800": variant === "default",
            "bg-green-100 text-green-800": variant === "success",
            "bg-yellow-100 text-yellow-800": variant === "warning",
            "bg-red-100 text-red-800": variant === "error",
            "bg-blue-100 text-blue-800": variant === "info",
          },
          className
        )}
        {...props}
      />
    );
  }
);

Badge.displayName = "Badge";

export function ScoreBadge({ score }: { score: number }) {
  let variant: BadgeProps["variant"] = "error";
  let label = "Faible";

  if (score >= 80) {
    variant = "success";
    label = "Excellent";
  } else if (score >= 60) {
    variant = "warning";
    label = "Bon";
  } else if (score >= 40) {
    variant = "info";
    label = "Moyen";
  }

  return (
    <Badge variant={variant}>
      {score.toFixed(0)}/100 - {label}
    </Badge>
  );
}

export function RecommendationBadge({
  action,
}: {
  action: "buy" | "watch" | "ignore";
}) {
  const config = {
    buy: { variant: "success" as const, label: "Acheter" },
    watch: { variant: "warning" as const, label: "Surveiller" },
    ignore: { variant: "error" as const, label: "Ignorer" },
  };

  const { variant, label } = config[action] || config.ignore;

  return <Badge variant={variant}>{label}</Badge>;
}
