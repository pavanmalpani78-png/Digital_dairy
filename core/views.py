from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from .models import Customer, MilkOrder, MilkTransaction, DeliveryBoy, UPIPayment, ShopkeeperProfile
from .forms import CustomerForm, MilkTransactionForm

def D(x, default="0"):
    try:
        if x is None:
            return Decimal(default)
        x = str(x).strip()
        if x == "":
            return Decimal(default)
        return Decimal(x)
    except (InvalidOperation, ValueError):
        return Decimal(default)

# ---------- BASIC PAGES ----------
@login_required
def dashboard(request):
    today = timezone.localdate()
    
    # Metrics
    total_customers = Customer.objects.filter(shopkeeper=request.user).count()
    
    today_orders = MilkOrder.objects.filter(shopkeeper=request.user, date=today)
    today_liters = today_orders.aggregate(Sum('total_liters'))['total_liters__sum'] or 0
    today_total = today_orders.aggregate(Sum('total'))['total__sum'] or 0
    
    pending_orders_count = MilkOrder.objects.filter(
        shopkeeper=request.user, 
        placed_by="CUSTOMER", 
        status="PENDING"
    ).count()
    
    recent_orders = MilkOrder.objects.filter(
        shopkeeper=request.user
    ).select_related('customer').order_by('-id')[:5]

    # Pass shop profile if it exists (for displaying shop name in dashboard)
    shop_profile = getattr(request.user, 'profile', None)

    context = {
        "total_customers": total_customers,
        "today_liters": today_liters,
        "today_total": today_total,
        "pending_orders_count": pending_orders_count,
        "recent_orders": recent_orders,
        "today": today,
        "shop_profile": shop_profile,
    }
    return render(request, "dashboard.html", context)

def home(request):
    return render(request, "home.html")

def login_page(request):
    if request.method == "POST":
        u = request.POST.get("username")
        p = request.POST.get("password")
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "login.html")

def signup_page(request):
    if request.method == "POST":
        u  = request.POST.get("username")
        p  = request.POST.get("password")
        cp = request.POST.get("confirm_password")

        if p != cp:
            messages.error(request, "Passwords do not match!")
            return render(request, "signup.html")

        if User.objects.filter(username=u).exists():
            messages.error(request, "Username is already taken. Please choose another.")
            return render(request, "signup.html")

        try:
            user = User.objects.create_user(username=u, password=p)
            # 🔒 Auto-create ShopkeeperProfile with shop_code = username
            ShopkeeperProfile.objects.create(user=user, shop_code=u)
            login(request, user)
            messages.success(request, f"Welcome {u}! Your shop account has been created.")
            return redirect("dashboard")
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")

    return render(request, "signup.html")

def logout_view(request):
    logout(request)
    return redirect("home")

def terms_page(request):
    return render(request, "terms.html")

# ---------- CUSTOMER CRUD (SHOPKEEPER) ----------
@login_required
def customer_page(request):
    customers = Customer.objects.filter(shopkeeper=request.user)
    return render(request, "customer.html", {"customers": customers})

@login_required
def add_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.shopkeeper = request.user
            c.save()
            return redirect("customer_page")
    else:
        form = CustomerForm()
    return render(request, "add_customer.html", {"form": form})

@login_required
def edit_customer(request, id):
    customer = get_object_or_404(Customer, id=id, shopkeeper=request.user)
    if request.method == "POST":
        customer.name = request.POST.get("name")
        customer.phone = request.POST.get("phone")
        customer.address = request.POST.get("address")
        customer.balance = request.POST.get("balance") or 0
        customer.login_phone = request.POST.get("login_phone")
        customer.login_password = request.POST.get("login_password")
        customer.save()
        return redirect("customer_page")
    return render(request, "edit_customer.html", {"customer": customer})

@login_required
def delete_customer(request, id):
    customer = get_object_or_404(Customer, id=id, shopkeeper=request.user)
    customer.delete()
    return redirect("customer_page")

# ---------- MILK ORDER (SHOPKEEPER) ----------
@login_required
def milk_order(request):
    selected_date = request.GET.get("date")
    if not selected_date:
        selected_date = timezone.localdate().isoformat()
    
    orders = MilkOrder.objects.filter(shopkeeper=request.user, date=selected_date).order_by("-id")
    return render(request, "milk_order.html", {
        "orders": orders,
        "selected_date": selected_date,
    })

@login_required
def add_milk_order(request):
    customers = Customer.objects.filter(shopkeeper=request.user).order_by("name")
    selected_date = request.GET.get("date") or timezone.localdate().isoformat()

    if request.method == "POST":
        customer_id = request.POST.get("customer")
        product_type = request.POST.get("product_type")
        date_str = request.POST.get("date") or selected_date
        brand = request.POST.get("brand") or None
        milk_type = request.POST.get("milk_type") or None
        pack_size = request.POST.get("pack_size") or None
        packets = request.POST.get("packets") or 0
        quantity = request.POST.get("quantity") or 0
        unit = request.POST.get("unit") or ""
        rate = request.POST.get("rate") or 0

        try:
            obj = MilkOrder(
                shopkeeper=request.user,
                customer_id=customer_id,
                product_type=product_type,
                date=date_str,
                brand=brand,
                milk_type=milk_type,
                pack_size=pack_size,
                packets=packets,
                quantity=quantity,
                unit=unit,
                rate=rate,
                placed_by="SHOPKEEPER",
                status="APPROVED",
            )
            obj.save()
            messages.success(request, f"Order for {obj.customer.name} on {obj.date} recorded successfully!")
            return redirect(f"/milkorder/?date={date_str}")
        except Exception as e:
            messages.error(request, f"Failed to save order: {str(e)}")
            return redirect("add_milk_order")

    return render(request, "add_milk_order.html", {
        "customers": customers,
        "selected_date": selected_date,
    })

@login_required
def edit_order(request, pk):
    order = get_object_or_404(MilkOrder, pk=pk, shopkeeper=request.user)
    customers = Customer.objects.filter(shopkeeper=request.user).order_by("name")

    if request.method == "POST":
        order.customer_id = request.POST.get("customer")
        order.product_type = request.POST.get("product_type")
        order.date = request.POST.get("date") or order.date

        if order.product_type == "MILK":
            order.brand = request.POST.get("brand") or None
            order.milk_type = request.POST.get("milk_type") or None
            order.pack_size = request.POST.get("pack_size") or None
            order.packets = int(request.POST.get("packets") or 0)

            order.quantity = Decimal("0")
            order.unit = ""
            order.rate = Decimal("0")
        else:
            order.quantity = D(request.POST.get("quantity"), "0")
            order.unit = request.POST.get("unit") or "KG"
            order.rate = D(request.POST.get("rate"), "0")

            order.brand = None
            order.milk_type = None
            order.pack_size = request.POST.get("pack_size") or None
            order.packets = int(request.POST.get("packets") or 0)

        order.save()
        return redirect(f"/milkorder/?date={order.date}")

    return render(request, "edit_order.html", {"order": order, "customers": customers})

@login_required
def delete_order(request, pk):
    order = get_object_or_404(MilkOrder, pk=pk, shopkeeper=request.user)
    d = order.date
    order.delete()
    return redirect(f"/milkorder/?date={d}")

# ---------- TRANSACTIONS ----------
@login_required
def transaction_page(request):
    transactions = MilkTransaction.objects.filter(shopkeeper=request.user).select_related("customer").order_by("-date", "-id")
    return render(request, "transaction.html", {"transactions": transactions})

@login_required
def add_transaction(request):
    if request.method == "POST":
        form = MilkTransactionForm(request.POST)
        if form.is_valid():
            t = form.save(commit=False)
            t.shopkeeper = request.user
            t.amount = D(t.qty, "0") * D(t.rate, "0")
            t.save()
            return redirect("transaction_page")
    else:
        form = MilkTransactionForm()
    return render(request, "add_transaction.html", {"form": form})

@login_required
def toggle_transaction_status(request, pk):
    if request.method == "POST":
        t = get_object_or_404(MilkTransaction, pk=pk, shopkeeper=request.user)
        t.payment_status = "UNPAID" if t.payment_status == "PAID" else "PAID"
        t.save()
    return redirect("transaction_page")

# API auto-fill
def customer_last_milk(request):
    customer_id = request.GET.get("customer_id")
    if not customer_id:
        return JsonResponse({"ok": False, "liters": 0, "rate": 0})

    order = (
        MilkOrder.objects.filter(customer_id=customer_id, product_type="MILK")
        .order_by("-date", "-id")
        .first()
    )

    if not order or order.total_liters == 0:
        return JsonResponse({"ok": True, "liters": 0, "rate": 0})

    rate_per_liter = Decimal(str(order.total)) / Decimal(str(order.total_liters))
    return JsonResponse({"ok": True, "liters": float(order.total_liters), "rate": float(rate_per_liter)})

# ---------- DAILY REPORT ----------
@login_required
def daily_milk_report(request):
    selected_date = request.GET.get("date") or timezone.localdate().isoformat()

    # 🔒 Always scope to the logged-in shopkeeper — never expose other shops' data
    orders = (
        MilkOrder.objects
        .filter(shopkeeper=request.user, date=selected_date)
        .select_related("customer")
        .order_by("-id")
    )

    totals = orders.aggregate(
        total_amount=Sum("total"),
        total_liters=Sum("total_liters"),
        total_qty=Sum("quantity"),
    )

    product_summary = (
        orders.values("product_type")
        .annotate(amount=Sum("total"))
        .order_by("product_type")
    )

    return render(request, "daily_report.html", {
        "selected_date": selected_date,
        "orders": orders,
        "totals": totals,
        "product_summary": product_summary,
    })

# ---------- BILL (HTML + PDF) ----------
from django.conf import settings

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

import os

from .models import Customer, MilkOrder


# 1️⃣ Bill home – select customer
@login_required
def bill_select_customer(request):
    customers = Customer.objects.filter(shopkeeper=request.user).order_by("name")

    if request.method == "POST":
        customer_id = request.POST.get("customer")
        start = request.POST.get("start_date")
        end = request.POST.get("end_date")
        url = f"/bill/view/{customer_id}/?start={start}&end={end}"
        return redirect(url)

    return render(request, "bill_select_customer.html", {
        "customers": customers
    })


# 2️⃣ Bill view (HTML)
@login_required
def bill_view(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id, shopkeeper=request.user)
    start_date = request.GET.get("start")
    end_date = request.GET.get("end")

    orders = MilkOrder.objects.filter(customer=customer).order_by("date", "id")
    if start_date:
        orders = orders.filter(date__gte=start_date)
    if end_date:
        orders = orders.filter(date__lte=end_date)

    totals = orders.aggregate(
        total_liters=Sum("total_liters"),
        total_qty=Sum("quantity"),
        total_amount=Sum("total"),
    )

    return render(request, "bill_view.html", {
        "customer": customer,
        "orders": orders,
        "start_date": start_date,
        "end_date": end_date,
        "total_liters": totals["total_liters"] or 0,
        "total_qty": totals["total_qty"] or 0,
        "total_amount": totals["total_amount"] or 0,
    })


# 3️⃣ Bill PDF (download)
@login_required
def bill_pdf(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id, shopkeeper=request.user)
    start_date = request.GET.get("start")
    end_date = request.GET.get("end")

    orders = MilkOrder.objects.filter(customer=customer).order_by("date", "id")
    if start_date:
        orders = orders.filter(date__gte=start_date)
    if end_date:
        orders = orders.filter(date__lte=end_date)

    totals = orders.aggregate(
        total_liters=Sum("total_liters"),
        total_amount=Sum("total"),
    )

    total_liters = totals["total_liters"] or 0
    grand_total = totals["total_amount"] or 0

    today = timezone.localdate()
    invoice_no = f"INV-{customer.id}-{today.strftime('%Y%m%d')}"

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Invoice_{customer.name}_{today}.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    def money(x):
        try:
            return f"₹ {float(x):.2f}"
        except Exception:
            return f"₹ {x}"

    # ---------- Header ----------
    c.setFillColorRGB(0.06, 0.25, 0.55)
    c.rect(0, height - 95, width, 95, stroke=0, fill=1)

    # optional logo
    logo_path = os.path.join(settings.BASE_DIR, "core", "static", "core", "logo.png")
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 40, height - 85, width=55, height=55, mask="auto")
        except Exception:
            pass

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(110, height - 55, "MILK KHATA - INVOICE")

    c.setFont("Helvetica", 10)
    c.drawString(110, height - 73, "Dairy Orders Billing System")

    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 40, height - 55, f"Invoice No: {invoice_no}")
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 40, height - 72, f"Date: {today}")

    c.setFillColor(colors.black)

    # ---------- Shop + Customer ----------
    y = height - 125
    c.setStrokeColor(colors.lightgrey)
    c.setFillColorRGB(0.97, 0.98, 1.0)
    c.rect(35, y - 90, width - 70, 90, stroke=1, fill=1)

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y - 25, "From (Shop)")
    c.drawString(width/2 + 10, y - 25, "Bill To (Customer)")

    c.setFont("Helvetica", 10)
    c.drawString(50, y - 42, "Milk Khata Dairy Store")
    c.drawString(50, y - 56, "Address: Your Shop Address")
    c.drawString(50, y - 70, "Phone: +91-XXXXXXXXXX")

    c.drawString(width/2 + 10, y - 42, f"Name: {customer.name}")
    c.drawString(width/2 + 10, y - 56, f"Phone: {customer.phone or '-'}")
    c.drawString(width/2 + 10, y - 70, f"Address: {customer.address or '-'}")

    y = y - 115

    # ---------- Table ----------
    table_left = 35
    table_right = width - 35
    row_h = 18

    columns = [
        ("Date", 55),
        ("Product", 65),
        ("Brand", 65),
        ("Type", 50),
        ("Pack", 45),
        ("Pkts", 35),
        ("Liters", 45),
        ("Total", 65),
    ]

    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.rect(table_left, y, table_right - table_left, row_h + 6, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)

    x = table_left + 8
    for title, w in columns:
        c.drawString(x, y + 6, title)
        x += w

    y -= (row_h + 6)

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)

    def new_page():
        nonlocal y
        c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(35, height - 40, "MILK KHATA - INVOICE")
        c.setFont("Helvetica", 10)
        c.drawString(35, height - 55, f"Customer: {customer.name}    Invoice: {invoice_no}    Date: {today}")
        y = height - 90

        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.rect(table_left, y, table_right - table_left, row_h + 6, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        x2 = table_left + 8
        for title, w in columns:
            c.drawString(x2, y + 6, title)
            x2 += w
        y -= (row_h + 6)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)

    alt = False
    for o in orders:
        if y < 140:
            new_page()

        if alt:
            c.setFillColorRGB(0.98, 0.99, 1.0)
            c.rect(table_left, y, table_right - table_left, row_h, stroke=0, fill=1)
        c.setFillColor(colors.black)
        alt = not alt

        x = table_left + 8
        c.drawString(x, y + 4, str(o.date)); x += columns[0][1]
        c.drawString(x, y + 4, str(o.product_type)); x += columns[1][1]
        c.drawString(x, y + 4, str(o.brand or "-")); x += columns[2][1]
        c.drawString(x, y + 4, str(o.milk_type or "-")); x += columns[3][1]
        c.drawString(x, y + 4, str(o.pack_size or "-")); x += columns[4][1]
        c.drawString(x, y + 4, str(o.packets or 0)); x += columns[5][1]
        c.drawString(x, y + 4, str(o.total_liters or 0)); x += columns[6][1]
        c.drawString(x, y + 4, money(o.total or 0)); x += columns[7][1]

        y -= row_h

    # ---------- Totals ----------
    y -= 10
    if y < 120:
        new_page()

    c.setStrokeColor(colors.lightgrey)
    c.setFillColorRGB(0.97, 0.98, 1.0)
    c.rect(width - 240, y - 55, 205, 55, stroke=1, fill=1)

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(width - 230, y - 20, f"Total Liters: {total_liters}")
    c.drawString(width - 230, y - 40, f"Grand Total: {money(grand_total)}")

    c.showPage()
    c.save()
    return response

# ---------- CUSTOMER PANEL ----------
def customer_home(request):
    return render(request, "customer_panel/home.html")

def customer_login(request):
    if request.method == "POST":
        phone     = (request.POST.get("phone") or "").strip()
        password  = (request.POST.get("password") or "").strip()
        shop_code = (request.POST.get("shop_code") or "").strip()

        # 🔒 Resolve the shopkeeper via ShopkeeperProfile.shop_code
        if shop_code:
            profile = ShopkeeperProfile.objects.filter(shop_code__iexact=shop_code).first()
            if not profile:
                messages.error(request, "Shop not found. Check your shop code.")
                return redirect("customer_login")
            customer = Customer.objects.filter(
                shopkeeper=profile.user,
                login_phone=phone,
                login_password=password
            ).first()
        else:
            # Fallback — no shop code provided
            customer = Customer.objects.filter(
                login_phone=phone,
                login_password=password
            ).first()

        if not customer:
            messages.error(request, "Invalid phone, password, or shop code.")
            return redirect("customer_login")

        # 🔒 Block inactive customers
        if not customer.is_active:
            messages.error(request, "Your account has been disabled. Please contact your dairy owner.")
            return redirect("customer_login")

        request.session["customer_id"]    = customer.id
        request.session["customer_name"]  = customer.name
        request.session["shopkeeper_id"]  = customer.shopkeeper_id
        return redirect("customer_dashboard")

    return render(request, "customer_panel/login.html")

def customer_dashboard(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("customer_login")

    # 🔒 Ensure this customer truly belongs to the shopkeeper stored in session
    shopkeeper_id = request.session.get("shopkeeper_id")
    customer = get_object_or_404(Customer, id=customer_id, shopkeeper_id=shopkeeper_id)

    recent_orders = MilkOrder.objects.filter(
        customer_id=customer_id,
        shopkeeper_id=shopkeeper_id      # extra guard: only THIS shop's orders
    ).order_by("-date", "-id")[:3]

    return render(request, "customer_panel/dashboard.html", {
        "customer": customer,
        "recent_orders": recent_orders
    })

def customer_logout(request):
    # 🔒 Clear ALL session keys set during customer login
    request.session.pop("customer_id", None)
    request.session.pop("customer_name", None)
    request.session.pop("shopkeeper_id", None)
    return redirect("home")

def customer_order_success(request):
    return render(request, "customer_panel/order_success.html")

def customer_place_order(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("customer_login")

    if request.method == "POST":
        product_type = request.POST.get("product_type")

        brand = request.POST.get("brand") or None
        milk_type = request.POST.get("milk_type") or None
        pack_size = request.POST.get("pack_size") or None
        packets = request.POST.get("packets") or 0

        quantity = D(request.POST.get("quantity"), "0")
        unit = (request.POST.get("unit") or "").strip()
        rate = D(request.POST.get("rate"), "0")
        date_str = request.POST.get("date")

        payment_method = request.POST.get("payment_method") or "COD"
        customer = get_object_or_404(Customer, id=customer_id)

        order_data = {
            "shopkeeper": customer.shopkeeper,
            "customer_id": customer_id,
            "product_type": product_type,
            "quantity": quantity,
            "unit": unit,
            "rate": rate,
            "brand": brand,
            "milk_type": milk_type,
            "pack_size": pack_size,
            "packets": packets,
            "payment_method": payment_method,
            "placed_by": "CUSTOMER",
            "status": "PENDING",
        }
        
        if date_str:
            order_data["date"] = date_str

        MilkOrder.objects.create(**order_data)
        return redirect("customer_order_success")

    return render(request, "customer_panel/place_order.html", {
        "customer_name": request.session.get("customer_name"),
        "selected_date": timezone.localdate().isoformat(),
    })

def customer_my_orders(request):
    customer_id = request.session.get("customer_id")
    shopkeeper_id = request.session.get("shopkeeper_id")
    if not customer_id:
        return redirect("customer_login")

    # 🔒 Scope to this customer AND their shopkeeper — no cross-shop leakage
    orders = MilkOrder.objects.filter(
        customer_id=customer_id,
        shopkeeper_id=shopkeeper_id
    ).order_by("-date", "-id")
    return render(request, "customer_panel/my_orders.html", {"orders": orders})

def customer_reorder(request, pk):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("customer_login")
        
    old_order = get_object_or_404(MilkOrder, pk=pk, customer_id=customer_id)
    
    # Create new order based on old one
    MilkOrder.objects.create(
        shopkeeper=old_order.shopkeeper,
        customer_id=customer_id,
        product_type=old_order.product_type,
        quantity=old_order.quantity,
        unit=old_order.unit,
        rate=old_order.rate,
        brand=old_order.brand,
        milk_type=old_order.milk_type,
        pack_size=old_order.pack_size,
        packets=old_order.packets,
        payment_method=old_order.payment_method,
        placed_by="CUSTOMER",
        status="PENDING",
        date=timezone.localdate()
    )
    
    messages.success(request, "Order repeated successfully! Please check your status.")
    return redirect("customer_my_orders")

def customer_statement(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("customer_login")

    customer = get_object_or_404(Customer, id=customer_id)

    # Use MilkOrders as the statement source (approved orders placed by/for this customer)
    orders = MilkOrder.objects.filter(
        customer=customer,
        status="APPROVED"
    ).order_by("-date", "-id")

    total_amount = orders.aggregate(Sum("total"))["total__sum"] or 0

    # Paid = orders marked as PAID in delivery
    total_paid = orders.filter(payment_status="PAID").aggregate(Sum("total"))["total__sum"] or 0
    total_unpaid = orders.filter(payment_status="UNPAID").aggregate(Sum("total"))["total__sum"] or 0

    return render(request, "customer_panel/statement.html", {
        "customer": customer,
        "orders": orders,
        "total_amount": total_amount,
        "total_paid": total_paid,
        "total_unpaid": total_unpaid,
    })

# ---------- SHOP: PENDING ORDERS + APPROVE/REJECT ----------
@login_required
def shop_pending_orders(request):
    orders = MilkOrder.objects.filter(shopkeeper=request.user, placed_by="CUSTOMER", status="PENDING").order_by("-date", "-id")
    # ✅ your template is in templates root => "pending_orders.html"
    return render(request, "pending_orders.html", {"orders": orders})

@login_required
def approve_order(request, pk):
    o = get_object_or_404(MilkOrder, pk=pk, shopkeeper=request.user)
    o.status = "APPROVED"
    o.save()
    return redirect("pending_orders")

@login_required
def reject_order(request, pk):
    o = get_object_or_404(MilkOrder, pk=pk, shopkeeper=request.user)
    o.status = "REJECTED"
    o.save()
    return redirect("pending_orders")

# UPI Payment view is disabled (Option A - removing payment from customer side)
def customer_upi_payment(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("customer_login")
    return redirect("customer_dashboard")

@login_required
def shop_delivery_dashboard(request):
    selected_date = request.GET.get("date") or timezone.localdate().isoformat()
    orders = MilkOrder.objects.filter(shopkeeper=request.user, date=selected_date).select_related("customer", "delivery_boy").order_by("-id")
    delivery_boys = DeliveryBoy.objects.filter(shopkeeper=request.user, is_active=True)
    
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        action = request.POST.get("action")
        
        # 🔒 Scope the order lookup to this shopkeeper to prevent IDOR attacks
        order = get_object_or_404(MilkOrder, id=order_id, shopkeeper=request.user)
        if action == "assign":
            boy_id = request.POST.get("delivery_boy")
            if boy_id:
                order.delivery_boy_id = boy_id
                order.delivery_status = "OUT_FOR_DELIVERY"
                order.save()
        elif action == "mark_delivered_paid" or action == "mark_delivered_unpaid":
            order.delivery_status = "DELIVERED"
            new_status = "PAID" if action == "mark_delivered_paid" else "UNPAID"
            order.payment_status = new_status
            order.save()
            
            # Create a matching transaction for bookkeeping
            qty = order.total_liters if order.product_type == "MILK" else order.quantity
            unit = "L" if order.product_type == "MILK" else order.unit
            
            MilkTransaction.objects.create(
                shopkeeper=request.user,
                customer=order.customer,
                product_type=order.product_type,
                qty=qty,
                unit=unit,
                rate=order.rate,
                amount=order.total,
                payment_status=new_status,
                note=f"Auto-generated from Delivery #{order.id}"
            )
            messages.success(request, f"Order #{order.id} marked as {new_status} and transaction recorded.")

        elif action == "cancel_assignment":
            order.delivery_status = "PENDING"
            order.delivery_boy = None
            order.payment_status = "UNPAID"
            order.save()
            messages.info(request, f"Order #{order.id} has been reset to Pending. Ready to reassign.")
            
        return redirect(f"/shop/deliveries/?date={selected_date}")
        
    return render(request, "delivery_dashboard.html", {
        "orders": orders,
        "delivery_boys": delivery_boys,
        "selected_date": selected_date
    })

# ---------- DRIVER MANAGEMENT ----------
@login_required
def driver_list(request):
    drivers = DeliveryBoy.objects.filter(shopkeeper=request.user)
    return render(request, "driver_list.html", {"drivers": drivers})

@login_required
def add_driver(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        if DeliveryBoy.objects.filter(shopkeeper=request.user, phone=phone).exists():
            messages.error(request, "Driver with this phone already exists.")
            return redirect("add_driver")
        
        DeliveryBoy.objects.create(
            shopkeeper=request.user,
            name=name,
            phone=phone,
            is_active=True
        )
        messages.success(request, f"Driver {name} added successfully!")
        return redirect("driver_list")
    return render(request, "add_driver.html")

@login_required
def delete_driver(request, pk):
    driver = get_object_or_404(DeliveryBoy, id=pk, shopkeeper=request.user)
    name = driver.name
    driver.delete()
    messages.success(request, f"Driver {name} removed.")
    return redirect("driver_list")


