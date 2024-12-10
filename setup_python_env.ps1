# Path to your Python executable
$pythonPath = "D:\glocal_energy_transition\fastapi_env\Scripts\python.exe"

# Ensure pip is up-to-date
Write-Output "Updating pip..."
& $pythonPath -m pip install --upgrade pip

# Define packages to install
$packages = @(
    "numpy",
    "pandas",
#    "matplotlib",
#    "scipy",
#    "requests",
	"gamspy"
)

# Install each package
foreach ($package in $packages) {
    Write-Output "Installing $package..."
    & $pythonPath -m pip install $package
}


Write-Output "Adding GAMSPy license..." # Adds Florian's Academic Network License
& $pythonPath -m gamspy install license 2c85ee4f-de02-42d5-9828-0c1a3977420c


Write-Output "Showing license:"
& $pythonPath -m gamspy show license

Write-Output "Showing solvers:"
& $pythonPath -m gamspy list solvers

Write-Output "For more info, incl. on uninstalling, adding more solvers, etc.: https://gamspy.readthedocs.io/en/latest/user/installation.html"

Write-Output "Setup complete!"
