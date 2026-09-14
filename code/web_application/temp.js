// Update an existing user
async function updateUser() {
    const idInput = document.getElementById('updateId');
    const nameInput = document.getElementById('updateName');
    const id = parseInt(idInput.value);
    const name = nameInput.value.trim();

    if (!id || !name) {
        alert('Please enter both User ID and new name');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: name })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update user');
        }

        const updatedUser = await response.json();
        console.log('Updated user:', updatedUser);

        // Clear inputs and reload users
        idInput.value = '';
        nameInput.value = '';
        await loadUsers();
        alert(`User ID ${id} updated successfully!`);
    } catch (error) {
        console.error('Error updating user:', error);
        alert('Failed to update user: ' + error.message);
    }
}
