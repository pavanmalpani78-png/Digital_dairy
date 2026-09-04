from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("login/", views.login_page, name="login"),
    path("signup/", views.signup_page, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("terms/", views.terms_page, name="terms"),
    path("settings/", views.settings_page, name="settings_page"),

    # Shopkeeper customers
    path("customers/", views.customer_page, name="customer_page"),
    path("customers/export/", views.export_customers_csv, name="export_customers_csv"),
    path("customer/add/", views.add_customer, name="add_customer"),
    path("customer/edit/<int:id>/", views.edit_customer, name="edit_customer"),
    path("customer/delete/<int:id>/", views.delete_customer, name="delete_customer"),

    # Orders (Shopkeeper)
    path('milkorder/', views.milk_order, name='milk_order'),
    path('milkorder/add/', views.add_milk_order, name='add_milk_order'),
    path("orders/edit/<int:pk>/", views.edit_order, name="edit_order"),
    path("orders/delete/<int:pk>/", views.delete_order, name="delete_order"),

    # Transactions
    path("transactions/", views.transaction_page, name="transaction_page"),
    path("transaction/add/", views.add_transaction, name="add_transaction"),
    path("transaction/toggle/<int:pk>/", views.toggle_transaction_status, name="toggle_transaction_status"),
    path("api/last-milk/", views.customer_last_milk, name="customer_last_milk"),

    # Report & Expenses
    path("report/daily/", views.daily_milk_report, name="daily_milk_report"),
    path("expenses/", views.expense_list, name="expense_list"),
    path("expense/add/", views.add_expense, name="add_expense"),
    path("expense/delete/<int:pk>/", views.delete_expense, name="delete_expense"),
    
    path("subscriptions/", views.subscription_list, name="subscription_list"),
    path("subscription/add/", views.add_subscription, name="add_subscription"),
    path("subscription/toggle/<int:pk>/", views.toggle_subscription, name="toggle_subscription"),
    # Bill
    path("bill/", views.bill_select_customer, name="bill_select_customer"),
    path("bill/view/<int:customer_id>/", views.bill_view, name="bill_view"),
    path("bill/pdf/<int:customer_id>/", views.bill_pdf, name="bill_pdf"),

    # Customer Panel
    path("c/", views.customer_home, name="customer_home"),
    path("c/dashboard/", views.customer_dashboard, name="customer_dashboard"),
    path("c/login/", views.customer_login, name="customer_login"),
    path("c/logout/", views.customer_logout, name="customer_logout"),
    path("c/order/", views.customer_place_order, name="customer_place_order"),
    path("c/my-orders/", views.customer_my_orders, name="customer_my_orders"),
    path("c/reorder/<int:pk>/", views.customer_reorder, name="customer_reorder"),
    path("c/statement/", views.customer_statement, name="customer_statement"),
    path("c/success/", views.customer_order_success, name="customer_order_success"),

    # Shop pending orders
    path("shop/pending-orders/", views.shop_pending_orders, name="pending_orders"),
    path("shop/approve/<int:pk>/", views.approve_order, name="approve_order"),
    path("shop/reject/<int:pk>/", views.reject_order, name="reject_order"),
    
    # UPI Payment (disabled - Option A: removed from customer side)
    
    # Delivery Dashboard (Shopkeeper)
    path("shop/deliveries/", views.shop_delivery_dashboard, name="shop_delivery_dashboard"),
    
    # Delivery Boy App (Public)
    path("run-sheet/<uuid:access_token>/", views.delivery_run_sheet, name="delivery_run_sheet"),
    path("run-sheet/<uuid:access_token>/mark/<int:order_id>/", views.mark_delivered, name="mark_delivered"),
    
    # Driver Management
    path("drivers/", views.driver_list, name="driver_list"),
    path("drivers/add/", views.add_driver, name="add_driver"),
    path("drivers/delete/<int:pk>/", views.delete_driver, name="delete_driver"),
]