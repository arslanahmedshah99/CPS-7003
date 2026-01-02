"""
Presentation layer - Command Line Interface for the Museum System.
Provides interactive menus and handles user interaction.
"""
import sys
from typing import Optional, Dict, Any
from backend.business_logic import (
    MuseumService, ExhibitService, VisitorService,
    MaintenanceService, ReportingService, BusinessException
)
from backend.security import (
    AuthenticationManager, AuthenticationError, AuthorizationError,
    ValidationError, SecurityException
)

class CLIInterface:
    """Command-line interface for the museum management system."""

    def __init__(self):
        self.current_user: Optional[Dict[str, Any]] = None
        self.running = True

    def clear_screen(self):
        """Clear the terminal screen."""
        print("\n" * 2)

    def display_header(self, title: str):
        """Display a formatted header."""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)

    def display_menu(self, options: list):
        """Display a menu with numbered options."""
        print()
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        print(f"  0. Back/Exit")
        print()

    def get_input(self, prompt: str, required: bool = True) -> str:
        """Get user input with validation."""
        while True:
            value = input(f"{prompt}: ").strip()
            if value or not required:
                return value
            print("  ⚠ This field is required. Please try again.")

    def get_int_input(self, prompt: str) -> Optional[int]:
        """Get integer input from user."""
        try:
            return int(self.get_input(prompt))
        except ValueError:
            print("  ⚠ Invalid number. Please try again.")
            return None

    def confirm_action(self, message: str) -> bool:
        """Ask user to confirm an action."""
        response = input(f"{message} (yes/no): ").strip().lower()
        return response in ['yes', 'y']

    def display_error(self, message: str):
        """Display an error message."""
        print(f"\n  ❌ Error: {message}\n")

    def display_success(self, message: str):
        """Display a success message."""
        print(f"\n  ✓ Success: {message}\n")

    def display_info(self, message: str):
        """Display an info message."""
        print(f"\n  ℹ {message}\n")

    # ==================== Authentication ====================

    def login_menu(self):
        """Handle user login."""
        self.display_header("HeritagePlus Museum System - Login")

        username = self.get_input("Username")
        password = self.get_input("Password")

        try:
            self.current_user = AuthenticationManager.authenticate(username, password)
            self.display_success(f"Welcome, {self.current_user['username']} ({self.current_user['role']})")
            return True
        except AuthenticationError as e:
            self.display_error(str(e))
            return False

    def create_account_menu(self):
        """Handle new user registration."""
        self.display_header("Create New Account")

        username = self.get_input("Username (min 3 characters)")
        password = self.get_input("Password (min 8 characters)")
        email = self.get_input("Email")

        print("\nAvailable roles: viewer, staff, curator, admin")
        role = self.get_input("Role (default: viewer)", required=False) or "viewer"

        try:
            AuthenticationManager.create_user(username, password, email, role)
            self.display_success("Account created successfully! Please login.")
        except (ValidationError, SecurityException) as e:
            self.display_error(str(e))

    # ==================== Main Menus ====================

    def main_menu(self):
        """Display and handle main menu."""
        while self.running:
            self.display_header(f"Main Menu - {self.current_user['username']} ({self.current_user['role']})")

            options = [
                "Museum Management",
                "Exhibit Management",
                "Visitor Management",
                "Maintenance Management",
                "Reports & Analytics",
                "Account Settings"
            ]

            self.display_menu(options)
            choice = self.get_input("Select option")

            try:
                if choice == '1':
                    self.museum_menu()
                elif choice == '2':
                    self.exhibit_menu()
                elif choice == '3':
                    self.visitor_menu()
                elif choice == '4':
                    self.maintenance_menu()
                elif choice == '5':
                    self.reports_menu()
                elif choice == '6':
                    self.account_menu()
                elif choice == '0':
                    if self.confirm_action("Are you sure you want to logout?"):
                        self.display_info("Logged out successfully.")
                        return
                else:
                    self.display_error("Invalid option. Please try again.")
            except (AuthorizationError, BusinessException, ValidationError) as e:
                self.display_error(str(e))

    # ==================== Museum Management ====================

    def museum_menu(self):
        """Museum management submenu."""
        while True:
            self.display_header("Museum Management")

            options = [
                "View All Museums",
                "Add New Museum",
                "View Museum Statistics",
                "View Museum Performance Report"
            ]

            self.display_menu(options)
            choice = self.get_input("Select option")

            try:
                if choice == '1':
                    self.view_museums()
                elif choice == '2':
                    self.add_museum()
                elif choice == '3':
                    self.view_museum_stats()
                elif choice == '4':
                    self.view_museum_report()
                elif choice == '0':
                    return
                else:
                    self.display_error("Invalid option.")
            except (AuthorizationError, BusinessException, ValidationError) as e:
                self.display_error(str(e))

    def view_museums(self):
        """Display all museums."""
        museums = MuseumService.get_all_museums(self.current_user['role'])

        print("\n  Museums:")
        print("  " + "-" * 50)
        for museum in museums:
            print(f"  [{museum['museum_id']}] {museum['name']} - {museum['city']}")

        input("\n  Press Enter to continue...")

    def add_museum(self):
        """Add a new museum."""
        name = self.get_input("Museum Name")
        city = self.get_input("City")

        MuseumService.create_museum(name, city, self.current_user['role'], self.current_user['user_id'])
        self.display_success(f"Museum '{name}' added successfully!")

    def view_museum_stats(self):
        """Display museum statistics."""
        stats = MuseumService.get_museum_statistics()

        print("\n  Museum Statistics:")
        print("  " + "-" * 70)
        print(f"  {'Museum':<30} {'Items':<10} {'Visits':<10} {'Maintenance':<10}")
        print("  " + "-" * 70)

        for stat in stats:
            print(f"  {stat['name']:<30} {stat['total_items']:<10} {stat['total_visits']:<10} {stat['total_maintenance']:<10}")

        input("\n  Press Enter to continue...")

    def view_museum_report(self):
        """Display detailed museum report."""
        museum_id = self.get_int_input("Enter Museum ID")
        if not museum_id:
            return

        report = ReportingService.generate_museum_performance_report(museum_id)

        print("\n  Museum Performance Report:")
        print("  " + "-" * 50)
        print(f"  Total Items: {report['stats'].get('total_items', 0)}")
        print(f"  Total Visits: {report['stats'].get('total_visits', 0)}")
        print(f"  Total Maintenance: {report['stats'].get('total_maintenance', 0)}")

        print("\n  Visitor Trends (Last 12 Months):")
        for trend in report['visitor_trends']:
            print(f"    {trend['month']}: {trend['visits']} visits")

        print("\n  Top Categories:")
        for cat in report['top_categories']:
            print(f"    {cat['category']}: {cat['count']} items")

        input("\n  Press Enter to continue...")

    # ==================== Exhibit Management ====================

    def exhibit_menu(self):
        """Exhibit management submenu."""
        while True:
            self.display_header("Exhibit Management")

            options = [
                "Add New Exhibit",
                "View Exhibits by Category",
                "View Popular Exhibits",
                "Change Exhibit Status"
            ]

            self.display_menu(options)
            choice = self.get_input("Select option")

            try:
                if choice == '1':
                    self.add_exhibit()
                elif choice == '2':
                    self.view_exhibits_by_category()
                elif choice == '3':
                    self.view_popular_exhibits()
                elif choice == '4':
                    self.change_exhibit_status()
                elif choice == '0':
                    return
                else:
                    self.display_error("Invalid option.")
            except (AuthorizationError, BusinessException, ValidationError) as e:
                self.display_error(str(e))

    def add_exhibit(self):
        """Add a new exhibit."""
        museum_id = self.get_int_input("Museum ID")
        if not museum_id:
            return

        title = self.get_input("Exhibit Title")
        category = self.get_input("Category")
        acquired = self.get_input("Acquisition Date (YYYY-MM-DD)")

        ExhibitService.add_exhibit(
            museum_id, title, category, acquired,
            self.current_user['role'], self.current_user['user_id']
        )
        self.display_success(f"Exhibit '{title}' added successfully!")

    def view_exhibits_by_category(self):
        """View exhibits filtered by category."""
        category = self.get_input("Category")

        exhibits = ExhibitService.get_exhibits_by_category(category, self.current_user['role'])

        print(f"\n  Exhibits in '{category}':")
        print("  " + "-" * 70)

        for exhibit in exhibits:
            print(f"  [{exhibit['item_id']}] {exhibit['title']} - {exhibit['museum_name']}")
            print(f"      Status: {exhibit['status']}, Acquired: {exhibit['acquired']}")

        input("\n  Press Enter to continue...")

    def view_popular_exhibits(self):
        """View most maintained exhibits."""
        exhibits = ExhibitService.get_popular_exhibits()

        print("\n  Most Maintained Exhibits:")
        print("  " + "-" * 50)

        for title, count in exhibits:
            print(f"  {title}: {count} maintenance actions")

        input("\n  Press Enter to continue...")

    def change_exhibit_status(self):
        """Change an exhibit's status."""
        item_id = self.get_int_input("Exhibit ID")
        if not item_id:
            return

        print("\n  Valid statuses: active, on_loan, in_restoration, retired")
        new_status = self.get_input("New Status")

        ExhibitService.change_exhibit_status(
            item_id, new_status,
            self.current_user['role'], self.current_user['user_id']
        )
        self.display_success("Exhibit status updated!")

    # ==================== Visitor Management ====================

    def visitor_menu(self):
        """Visitor management submenu."""
        while True:
            self.display_header("Visitor Management")

            options = [
                "Register New Visitor",
                "Record Museum Visit",
                "View Frequent Visitors",
                "Get Visitor Recommendations"
            ]

            self.display_menu(options)
            choice = self.get_input("Select option")

            try:
                if choice == '1':
                    self.register_visitor()
                elif choice == '2':
                    self.record_visit()
                elif choice == '3':
                    self.view_frequent_visitors()
                elif choice == '4':
                    self.get_recommendations()
                elif choice == '0':
                    return
                else:
                    self.display_error("Invalid option.")
            except (AuthorizationError, BusinessException, ValidationError) as e:
                self.display_error(str(e))

    def register_visitor(self):
        """Register a new visitor."""
        full_name = self.get_input("Full Name")
        email = self.get_input("Email")
        phone = self.get_input("Phone (optional)", required=False)

        VisitorService.register_visitor(
            full_name, email, phone if phone else None,
            self.current_user['role'], self.current_user['user_id']
        )
        self.display_success(f"Visitor '{full_name}' registered successfully!")

    def record_visit(self):
        """Record a museum visit."""
        guest_id = self.get_int_input("Visitor ID")
        if not guest_id:
            return

        museum_id = self.get_int_input("Museum ID")
        if not museum_id:
            return

        visited_on = self.get_input("Visit Date (YYYY-MM-DD)")
        duration = self.get_input("Duration in minutes (optional)", required=False)

        VisitorService.record_visit(
            guest_id, museum_id, visited_on,
            int(duration) if duration else None,
            self.current_user['role'], self.current_user['user_id']
        )
        self.display_success("Visit recorded successfully!")

    def view_frequent_visitors(self):
        """View frequent visitors."""
        visitors = VisitorService.get_frequent_visitors()

        print("\n  Frequent Visitors:")
        print("  " + "-" * 70)
        print(f"  {'Name':<30} {'Email':<30} {'Visits':<10}")
        print("  " + "-" * 70)

        for visitor in visitors:
            print(f"  {visitor['full_name']:<30} {visitor['email']:<30} {visitor['total_visits']:<10}")

        input("\n  Press Enter to continue...")

    def get_recommendations(self):
        """Get museum recommendations for a visitor."""
        guest_id = self.get_int_input("Visitor ID")
        if not guest_id:
            return

        recommendations = VisitorService.get_visitor_recommendations(guest_id)

        print("\n  Recommended Museums:")
        print("  " + "-" * 50)

        for rec in recommendations:
            print(f"  {rec['name']} ({rec['city']}) - {rec['item_count']} items")

        input("\n  Press Enter to continue...")

    # ==================== Maintenance Management ====================

    def maintenance_menu(self):
        """Maintenance management submenu."""
        while True:
            self.display_header("Maintenance Management")

            options = [
                "Schedule Maintenance",
                "View Upcoming Maintenance",
                "View Items Needing Maintenance",
                "Maintenance Cost Analysis"
            ]

            self.display_menu(options)
            choice = self.get_input("Select option")

            try:
                if choice == '1':
                    self.schedule_maintenance()
                elif choice == '2':
                    self.view_upcoming_maintenance()
                elif choice == '3':
                    self.view_items_needing_maintenance()
                elif choice == '4':
                    self.maintenance_cost_analysis()
                elif choice == '0':
                    return
                else:
                    self.display_error("Invalid option.")
            except (AuthorizationError, BusinessException, ValidationError) as e:
                self.display_error(str(e))

    def schedule_maintenance(self):
        """Schedule maintenance for an exhibit."""
        item_id = self.get_int_input("Exhibit ID")
        if not item_id:
            return

        task = self.get_input("Task Description")
        done_on = self.get_input("Completion Date (YYYY-MM-DD)")
        technician = self.get_input("Technician Name")
        cost = self.get_input("Cost (optional)", required=False)

        MaintenanceService.schedule_maintenance(
            item_id, task, done_on, technician,
            float(cost) if cost else None,
            self.current_user['role'], self.current_user['user_id']
        )
        self.display_success("Maintenance scheduled successfully!")

    def view_upcoming_maintenance(self):
        """View upcoming maintenance."""
        schedule = MaintenanceService.get_maintenance_schedule()

        print("\n  Upcoming Maintenance (Next 30 Days):")
        print("  " + "-" * 70)

        for item in schedule:
            print(f"  [{item['done_on']}] {item['title']}")
            print(f"      Task: {item['task']}, Technician: {item['technician']}")

        input("\n  Press Enter to continue...")

    def view_items_needing_maintenance(self):
        """View items that need maintenance."""
        items = MaintenanceService.get_items_needing_maintenance()

        print("\n  Items Needing Maintenance:")
        print("  " + "-" * 70)

        for item in items:
            last_maint = item['last_maintenance'] or "Never"
            print(f"  [{item['item_id']}] {item['title']} - {item['museum_name']}")
            print(f"      Last Maintenance: {last_maint}")

        input("\n  Press Enter to continue...")

    def maintenance_cost_analysis(self):
        """Analyze maintenance costs."""
        start = self.get_input("Start Date (YYYY-MM-DD)")
        end = self.get_input("End Date (YYYY-MM-DD)")

        analysis = MaintenanceService.get_maintenance_cost_analysis(start, end)

        print("\n  Maintenance Cost Analysis:")
        print("  " + "-" * 50)
        print(f"  Total Tasks: {analysis['total_tasks']}")
        print(f"  Total Cost: ${analysis['total_cost']:.2f}")
        print(f"  Average Cost: ${analysis['avg_cost']:.2f}")
        print(f"  Min Cost: ${analysis['min_cost'] or 0:.2f}")
        print(f"  Max Cost: ${analysis['max_cost'] or 0:.2f}")

        input("\n  Press Enter to continue...")

    # ==================== Reports ====================

    def reports_menu(self):
        """Reports and analytics submenu."""
        while True:
            self.display_header("Reports & Analytics")

            options = [
                "Executive Summary",
                "Museum Performance Report",
                "Maintenance Summary"
            ]

            self.display_menu(options)
            choice = self.get_input("Select option")

            try:
                if choice == '1':
                    self.executive_summary()
                elif choice == '2':
                    self.view_museum_report()
                elif choice == '3':
                    self.maintenance_summary()
                elif choice == '0':
                    return
                else:
                    self.display_error("Invalid option.")
            except Exception as e:
                self.display_error(str(e))

    def executive_summary(self):
        """Display executive summary."""
        summary = ReportingService.generate_executive_summary()

        print("\n  Executive Summary:")
        print("  " + "-" * 50)
        print(f"  Total Museums: {summary['summary'].get('total_museums', 0)}")
        print(f"  Total Exhibits: {summary['summary'].get('total_items', 0)}")
        print(f"  Total Visitors: {summary['summary'].get('total_visitors', 0)}")
        print(f"  Visits (Last Month): {summary['recent_activity'].get('visits_last_month', 0)}")

        input("\n  Press Enter to continue...")

    def maintenance_summary(self):
        """Display maintenance summary."""
        summary = MaintenanceService.summary()

        print("\n  Maintenance Summary by Exhibit:")
        print("  " + "-" * 50)

        for title, total in summary:
            print(f"  {title}: {total} maintenance actions")

        input("\n  Press Enter to continue...")

    # ==================== Account Settings ====================

    def account_menu(self):
        """Account settings submenu."""
        while True:
            self.display_header("Account Settings")

            options = [
                "View Profile",
                "Change Password"
            ]

            self.display_menu(options)
            choice = self.get_input("Select option")

            try:
                if choice == '1':
                    self.view_profile()
                elif choice == '2':
                    self.change_password()
                elif choice == '0':
                    return
                else:
                    self.display_error("Invalid option.")
            except (AuthenticationError, ValidationError) as e:
                self.display_error(str(e))

    def view_profile(self):
        """Display user profile."""
        print("\n  User Profile:")
        print("  " + "-" * 50)
        print(f"  Username: {self.current_user['username']}")
        print(f"  Email: {self.current_user['email']}")
        print(f"  Role: {self.current_user['role']}")

        input("\n  Press Enter to continue...")

    def change_password(self):
        """Change user password."""
        old_password = self.get_input("Current Password")
        new_password = self.get_input("New Password (min 8 characters)")
        confirm_password = self.get_input("Confirm New Password")

        if new_password != confirm_password:
            self.display_error("Passwords do not match!")
            return

        AuthenticationManager.change_password(
            self.current_user['user_id'],
            old_password,
            new_password
        )
        self.display_success("Password changed successfully!")

    # ==================== Main Runner ====================

    def run(self):
        """Run the CLI application."""
        self.display_header("Welcome to HeritagePlus Museum System")

        while True:
            print("\n  1. Login")
            print("  2. Create Account")
            print("  0. Exit")

            choice = self.get_input("\nSelect option")

            if choice == '1':
                if self.login_menu():
                    self.main_menu()
                    self.current_user = None
            elif choice == '2':
                self.create_account_menu()
            elif choice == '0':
                self.display_info("Thank you for using HeritagePlus Museum System!")
                sys.exit(0)
            else:
                self.display_error("Invalid option.")

def main():
    """Entry point for the CLI application."""
    app = CLIInterface()
    app.run()

if __name__ == "__main__":
    main()

