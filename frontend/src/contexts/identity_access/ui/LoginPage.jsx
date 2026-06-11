import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/identity_access";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { getApiErrorMessage } from "@/shared/lib/utils";
import { toast } from "sonner";
import { Shield, Eye, EyeOff } from "lucide-react";

const _store = typeof sessionStorage !== 'undefined' ? sessionStorage : localStorage;
const AUTH_SESSION_NOTICE_KEY = 'iems_auth_notice';
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateCredentials(emailValue, passwordValue) {
	const nextErrors = {};

	if (!emailValue) {
		nextErrors.email = "Email is required";
	} else if (!EMAIL_PATTERN.test(emailValue)) {
		nextErrors.email = "Enter a valid email address";
	}

	if (!passwordValue) {
		nextErrors.password = "Password is required";
	}

	return nextErrors;
}

const LoginPage = () => {
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [showPassword, setShowPassword] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const [errors, setErrors] = useState({});
	const [authError, setAuthError] = useState("");
	const { login, user } = useAuth();
	const navigate = useNavigate();

	useEffect(() => {
		try {
			const authNotice = _store.getItem(AUTH_SESSION_NOTICE_KEY);
			if (authNotice) {
				_store.removeItem(AUTH_SESSION_NOTICE_KEY);
				toast.error(authNotice);
			}
		} catch { }
	}, []);

	useEffect(() => {
		if (user) {
			navigate("/");
		}
	}, [user, navigate]);

	const handleLogin = async (e) => {
		e.preventDefault();
		const formData = new FormData(e.currentTarget);
		const emailValue = String(formData.get("email") ?? email).trim();
		const passwordValue = String(formData.get("password") ?? password);
		const nextErrors = validateCredentials(emailValue, passwordValue);

		setErrors(nextErrors);
		setAuthError("");

		if (Object.keys(nextErrors).length > 0) {
			toast.error("Check the highlighted fields and try again");
			return;
		}

		setIsLoading(true);

		try {
			const userData = await login(emailValue, passwordValue);
			toast.success(`Welcome, ${userData.name}!`);
			navigate("/");
		} catch (error) {
			const message = getApiErrorMessage(error, "Invalid credentials");
			setAuthError(message);
			toast.error(message);
		} finally {
			setIsLoading(false);
		}
	};

	return (
		<div className="min-h-screen w-full bg-slate-50 flex items-center justify-center p-4">
			<Card className="w-full max-w-md shadow-xl border-0">
				<CardHeader className="text-center pb-2">
					<div className="flex items-center justify-center gap-2 mb-4">
						<Shield className="w-8 h-8 text-blue-600" />
					</div>
					<CardTitle className="text-lg sm:text-xl leading-tight">
						MADC Employee Management Portal
					</CardTitle>
					<CardDescription className="text-xs sm:text-sm">
						MADC-HRMS  -  Integrated Employee Lifecycle Workflow
					</CardDescription>
				</CardHeader>

				<CardContent>
					<form onSubmit={handleLogin} className="space-y-4" noValidate>
						{authError && (
							<div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert" data-testid="login-auth-error">
								{authError}
							</div>
						)}
						<div className="space-y-2">
							<Label htmlFor="email">Email</Label>
							<Input
								id="email"
								name="email"
								type="email"
								placeholder="your.email@iems.gov.in"
								value={email}
								onChange={(e) => {
									setEmail(e.target.value);
									if (errors.email) {
										setErrors((current) => ({ ...current, email: "" }));
									}
									if (authError) {
										setAuthError("");
									}
								}}
								required
								autoComplete="email"
								aria-invalid={Boolean(errors.email)}
								aria-describedby={errors.email ? "login-email-error" : undefined}
								className={errors.email ? "border-red-300 focus-visible:ring-red-400" : undefined}
								data-testid="login-email-input"
							/>
							{errors.email && (
								<p id="login-email-error" className="text-xs text-red-600" role="alert">
									{errors.email}
								</p>
							)}
						</div>

						<div className="space-y-2">
							<Label htmlFor="password">Password</Label>
							<div className="relative">
								<Input
									id="password"
									name="password"
									type={showPassword ? "text" : "password"}
									placeholder="Enter password"
									value={password}
									onChange={(e) => {
										setPassword(e.target.value);
										if (errors.password) {
											setErrors((current) => ({ ...current, password: "" }));
										}
										if (authError) {
											setAuthError("");
										}
									}}
									required
									autoComplete="current-password"
									aria-invalid={Boolean(errors.password)}
									aria-describedby={errors.password ? "login-password-error" : undefined}
									className={errors.password ? "border-red-300 pr-10 focus-visible:ring-red-400" : "pr-10"}
									data-testid="login-password-input"
								/>
								<button
									type="button"
									onClick={() => setShowPassword(!showPassword)}
									className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
									aria-label={showPassword ? "Hide password" : "Show password"}
									title={showPassword ? "Hide password" : "Show password"}
									data-testid="login-password-visibility-toggle"
								>
									{showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
								</button>
							</div>
							{errors.password && (
								<p id="login-password-error" className="text-xs text-red-600" role="alert">
									{errors.password}
								</p>
							)}
						</div>

						<Button
							type="submit"
							className="w-full bg-slate-900 hover:bg-slate-800"
							disabled={isLoading}
							data-testid="login-submit-btn"
						>
							{isLoading ? "Signing in..." : "Sign in"}
						</Button>
					</form>

					<div className="mt-4 pt-4 border-t text-center">
						<p className="text-[11px] text-slate-400 mt-2">&copy; {new Date().getFullYear()} MADC-HRMS &mdash; Mara Autonomous District Council</p>
					</div>
				</CardContent>
			</Card>
		</div>
	);
};

export default LoginPage;