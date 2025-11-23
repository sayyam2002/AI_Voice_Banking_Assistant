async function loadAccounts() {
    const accounts = await api("/accounts/balance");
    const container = document.getElementById("accounts");

    container.innerHTML = "";

    accounts.forEach(acc => {
        container.innerHTML += `
        <div class="card">
            <h3>${acc.account_type}</h3>
            <p>Balance: $${acc.balance}</p>
            <p>Acc: ${acc.account_number}</p>
        </div>`;
    });
}

loadAccounts();
