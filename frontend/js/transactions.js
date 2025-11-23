async function loadTransactions() {
    const data = await api("/transactions/");

    const tbody = document.querySelector("#txTable tbody");
    tbody.innerHTML = "";

    data.forEach(tx => {
        tbody.innerHTML += `
          <tr>
            <td>${tx.date}</td>
            <td>${tx.description}</td>
            <td>${tx.amount}</td>
            <td>${tx.type}</td>
          </tr>`;
    });
}

loadTransactions();
