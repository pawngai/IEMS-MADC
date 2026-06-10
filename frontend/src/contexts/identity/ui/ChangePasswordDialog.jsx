import { useState } from "react";
import { authAPI } from "@/contexts/identity/api/authApi";
import { getApiErrorMessage } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
} from "@/shared/ui/dialog";
import { toast } from "sonner";
import { Eye, EyeOff } from "lucide-react";

const ChangePasswordDialog = ({ open, onOpenChange, onLogout }) => {
	const [currentPassword, setCurrentPassword] = useState("");
	const [newPassword, setNewPassword] = useState("");
	const [confirmPassword, setConfirmPassword] = useState("");
	const [showCurrent, setShowCurrent] = useState(false);
	const [showNew, setShowNew] = useState(false);
	const [isSubmitting, setIsSubmitting] = useState(false);

	const reset = () => {
		setCurrentPassword("");
		setNewPassword("");
		setConfirmPassword("");
		setShowCurrent(false);
		setShowNew(false);
	};

	const handleSubmit = async (e) => {
		e.preventDefault();

		if (newPassword.length < 8) {
			toast.error("New password must be at least 8 characters");
			return;
		}
		if (newPassword !== confirmPassword) {
			toast.error("New passwords do not match");
			return;
		}
		if (newPassword === currentPassword) {
			toast.error("New password must differ from the current one");
			return;
		}

		setIsSubmitting(true);
		try {
			await authAPI.changePassword({
				current_password: currentPassword,
				new_password: newPassword,
			});
			toast.success("Password changed successfully. Please sign in again.");
			reset();
			onOpenChange(false);
			onLogout();
		} catch (error) {
			toast.error(getApiErrorMessage(error, "Failed to change password"));
		} finally {
			setIsSubmitting(false);
		}
	};

	return (
		<Dialog
			open={open}
			onOpenChange={(v) => {
				if (!v) reset();
				onOpenChange(v);
			}}
		>
			<DialogContent className="max-w-md">
				<DialogHeader>
					<DialogTitle>Change Password</DialogTitle>
					<DialogDescription>
						Enter your current password and choose a new one. You will be signed
						out after changing your password.
					</DialogDescription>
				</DialogHeader>

				<form onSubmit={handleSubmit} className="space-y-4">
					<div className="space-y-1.5">
						<Label htmlFor="cp-current">Current Password</Label>
						<div className="relative">
							<Input
								id="cp-current"
								type={showCurrent ? "text" : "password"}
								value={currentPassword}
								onChange={(e) => setCurrentPassword(e.target.value)}
								placeholder="Enter your current password"
								required
							/>
							<button
								type="button"
								className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
								onClick={() => setShowCurrent(!showCurrent)}
								tabIndex={-1}
							>
								{showCurrent ? (
									<EyeOff className="w-4 h-4" />
								) : (
									<Eye className="w-4 h-4" />
								)}
							</button>
						</div>
					</div>

					<div className="space-y-1.5">
						<Label htmlFor="cp-new">New Password</Label>
						<div className="relative">
							<Input
								id="cp-new"
								type={showNew ? "text" : "password"}
								value={newPassword}
								onChange={(e) => setNewPassword(e.target.value)}
								placeholder="At least 8 characters"
								minLength={8}
								required
							/>
							<button
								type="button"
								className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
								onClick={() => setShowNew(!showNew)}
								tabIndex={-1}
							>
								{showNew ? (
									<EyeOff className="w-4 h-4" />
								) : (
									<Eye className="w-4 h-4" />
								)}
							</button>
						</div>
					</div>

					<div className="space-y-1.5">
						<Label htmlFor="cp-confirm">Confirm New Password</Label>
						<Input
							id="cp-confirm"
							type="password"
							value={confirmPassword}
							onChange={(e) => setConfirmPassword(e.target.value)}
							placeholder="Repeat new password"
							required
						/>
						{confirmPassword && newPassword !== confirmPassword && (
							<p className="text-xs text-red-500">Passwords do not match</p>
						)}
					</div>

					<Button type="submit" className="w-full" disabled={isSubmitting}>
						{isSubmitting ? "Updating..." : "Update Password"}
					</Button>
				</form>
			</DialogContent>
		</Dialog>
	);
};

export default ChangePasswordDialog;
