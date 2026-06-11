import { useState } from "react";
import { authAPI } from "@/contexts/identity_access/api/authApi";
import { getApiErrorMessage } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { toast } from "sonner";
import { Eye, EyeOff, Lock } from "lucide-react";

const ForceChangePasswordDialog = ({ user, onPasswordChanged, onLogout }) => {
	const [currentPassword, setCurrentPassword] = useState("");
	const [newPassword, setNewPassword] = useState("");
	const [confirmPassword, setConfirmPassword] = useState("");
	const [showCurrent, setShowCurrent] = useState(false);
	const [showNew, setShowNew] = useState(false);
	const [isSubmitting, setIsSubmitting] = useState(false);

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
			toast.success("Password changed successfully! Welcome aboard.");
			onPasswordChanged();
		} catch (error) {
			toast.error(getApiErrorMessage(error, "Failed to change password"));
		} finally {
			setIsSubmitting(false);
		}
	};

	return (
		<div className="fixed inset-0 z-[100] bg-slate-900/80 flex items-center justify-center p-4">
			<Card className="w-full max-w-md shadow-2xl border-0">
				<CardHeader className="text-center pb-2">
					<div className="flex items-center justify-center gap-2 mb-3">
						<div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center">
							<Lock className="w-6 h-6 text-amber-600" />
						</div>
					</div>
					<CardTitle className="text-lg">Change Your Password</CardTitle>
					<CardDescription>
						Welcome, <strong>{user?.name}</strong>! Your account was created with
						a temporary password. Please set a new password to continue.
					</CardDescription>
				</CardHeader>

				<CardContent>
					<form onSubmit={handleSubmit} className="space-y-4">
						<div className="space-y-1.5">
							<Label htmlFor="current-pw">Temporary Password</Label>
							<div className="relative">
								<Input
									id="current-pw"
									type={showCurrent ? "text" : "password"}
									value={currentPassword}
									onChange={(e) => setCurrentPassword(e.target.value)}
									placeholder="Enter your temporary password"
									required
								/>
								<button
									type="button"
									className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
									onClick={() => setShowCurrent(!showCurrent)}
									tabIndex={-1}
								>
									{showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
								</button>
							</div>
						</div>

						<div className="space-y-1.5">
							<Label htmlFor="new-pw">New Password</Label>
							<div className="relative">
								<Input
									id="new-pw"
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
									{showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
								</button>
							</div>
						</div>

						<div className="space-y-1.5">
							<Label htmlFor="confirm-pw">Confirm New Password</Label>
							<Input
								id="confirm-pw"
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
							{isSubmitting ? "Changing..." : "Set New Password & Continue"}
						</Button>

						<button
							type="button"
							className="w-full text-sm text-slate-400 hover:text-slate-600 mt-2"
							onClick={onLogout}
						>
							Log out instead
						</button>
					</form>
				</CardContent>
			</Card>
		</div>
	);
};

export default ForceChangePasswordDialog;
