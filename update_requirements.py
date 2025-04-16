# save as update_requirements.py
import pkg_resources

# Read the existing requirements file
with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f.readlines() if line.strip()]

# Create a dict of installed package versions
installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}

# Update requirements with versions
updated_requirements = []
for req in requirements:
    package = req.split('==')[0].split('>')[0].split('<')[0].split('~=')[0].strip()
    if package in installed:
        updated_requirements.append(f"{package}=={installed[package]}")
    else:
        updated_requirements.append(req)
        print(f"Warning: Package {package} not found in the environment")

# Write the updated requirements
with open('requirements_updated.txt', 'w') as f:
    f.write('\n'.join(updated_requirements))

print("Updated requirements saved to requirements_updated.txt")