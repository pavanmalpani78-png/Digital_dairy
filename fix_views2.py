with open("core/views.py", "r", encoding="utf8") as f:
    text = f.read()

# Fix form saves
text = text.replace(
    'if form.is_valid():\n            form.save()',
    'if form.is_valid():\n            c = form.save(commit=False)\n            c.shopkeeper = request.user\n            c.save()'
)

text = text.replace(
    't = form.save(commit=False)\n            t.amount = D(t.qty, "0") * D(t.rate, "0")\n            t.save()',
    't = form.save(commit=False)\n            t.shopkeeper = request.user\n            t.amount = D(t.qty, "0") * D(t.rate, "0")\n            t.save()'
)

text = text.replace(
    'obj = MilkOrder(\n            customer_id=customer_id,',
    'obj = MilkOrder(\n            shopkeeper=request.user,\n            customer_id=customer_id,'
)

text = text.replace(
    'def login_page(request):\n    if request.method == "POST":\n        return redirect("home")\n    return render(request, "login.html")',
    'def login_page(request):\n    if request.method == "POST":\n        u = request.POST.get("username")\n        p = request.POST.get("password")\n        user = authenticate(request, username=u, password=p)\n        if user is not None:\n            login(request, user)\n            return redirect("dashboard")\n        else:\n            messages.error(request, "Invalid username or password.")\n    return render(request, "login.html")'
)

text = text.replace(
    'def signup_page(request):\n    if request.method == "POST":\n        return redirect("home")\n    return render(request, "signup.html")',
    'def signup_page(request):\n    if request.method == "POST":\n        u = request.POST.get("username")\n        p = request.POST.get("password")\n        if User.objects.filter(username=u).exists():\n            messages.error(request, "Username taken.")\n            return redirect("signup")\n        user = User.objects.create_user(username=u, password=p)\n        login(request, user)\n        return redirect("dashboard")\n    return render(request, "signup.html")\n\ndef logout_view(request):\n    logout(request)\n    return redirect("home")'
)

with open("core/views.py", "w", encoding="utf8") as f:
    f.write(text)
