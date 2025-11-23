async function makeTransfer() {
    const recipient = document.getElementById("recipient").value;
    const amount = document.getElementById("amount").value;
    const pin = document.getElementById("pin").value;

    try {
        const res = await api("/transfer", "POST", { recipient, amount, pin });
        document.getElementById("result").innerText = res.message;
    } catch (err) {
        document.getElementById("result").innerText = "Transfer failed";
    }
}
