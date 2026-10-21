document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-dismiss]').forEach(btn => btn.addEventListener('click', () => btn.closest('.message')?.remove()));
  const menu = document.querySelector('[data-menu-toggle]');
  const sidebar = document.querySelector('#sidebar');
  menu?.addEventListener('click', () => sidebar?.classList.toggle('open'));

  const chart = document.querySelector('#revenue-chart');
  if (chart) {
    const data = JSON.parse(chart.dataset.chart || '[]');
    const max = Math.max(...data.map(item => item.value), 1);
    chart.innerHTML = data.map(item => {
      const height = Math.max((item.value / max) * 100, item.value ? 4 : 1);
      const label = item.label.slice(5).replace('-', '/');
      return `<div class="bar-col" title="KES ${Math.round(item.value).toLocaleString()}"><div class="bar" style="height:${height}%"></div><span class="bar-label">${label}</span></div>`;
    }).join('');
  }

  const orderForm = document.querySelector('#order-form');
  if (orderForm) {
    const cart = {};
    const empty = document.querySelector('#cart-empty');
    const lines = document.querySelector('#cart-lines');
    const totalNode = document.querySelector('#order-total');
    const itemsInput = orderForm.querySelector('[name="items_json"]');
    const amountInput = orderForm.querySelector('[name="payment_amount"]');
    const money = value => Number(value).toLocaleString('en-KE', {maximumFractionDigits: 0});
    const renderCart = () => {
      const values = Object.values(cart);
      empty.style.display = values.length ? 'none' : 'block';
      lines.innerHTML = values.map(item => `<div class="cart-line"><div class="cart-line-main"><strong>${item.name}</strong><small>KES ${money(item.price)} each</small></div><div class="cart-line-side"><strong>KES ${money(item.price * item.quantity)}</strong><div class="qty-control"><button type="button" data-minus="${item.id}" aria-label="Reduce ${item.name}">−</button><span>${item.quantity}</span><button type="button" data-plus="${item.id}" aria-label="Add ${item.name}">＋</button></div></div></div>`).join('');
      const total = values.reduce((sum, item) => sum + item.price * item.quantity, 0);
      totalNode.textContent = money(total);
      itemsInput.value = JSON.stringify(values.map(item => ({product_id: item.id, quantity: item.quantity})));
      if (!amountInput.value && total) amountInput.placeholder = `KES ${money(total)} calculated total`;
    };
    document.querySelectorAll('[data-product-id]').forEach(button => button.addEventListener('click', () => {
      const id = button.dataset.productId;
      cart[id] = cart[id] || {id: Number(id), name: button.dataset.productName, price: Number(button.dataset.productPrice), quantity: 0};
      cart[id].quantity += 1; renderCart();
    }));
    lines?.addEventListener('click', event => {
      const id = event.target.dataset.minus || event.target.dataset.plus;
      if (!id || !cart[id]) return;
      if (event.target.dataset.minus) cart[id].quantity -= 1; else cart[id].quantity += 1;
      if (cart[id].quantity <= 0) delete cart[id];
      renderCart();
    });
    renderCart();
  }
});
