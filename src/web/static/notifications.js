// Notification handling for motor status alerts

const NOTIFICATION_TYPES = {
    WARNING: 'warning',
    ERROR: 'error',
    INFO: 'info'
};

const NOTIFICATION_TIMEOUT = 5000; // 5 seconds

class NotificationManager {
    constructor() {
        this.container = this.createContainer();
        this.notifications = new Map();
    }

    createContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(container);
        return container;
    }

    createNotification(message, type = NOTIFICATION_TYPES.INFO, motorId = null) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            padding: 12px 20px;
            border-radius: 6px;
            background: #2a2a2a;
            color: #fff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 300px;
            transform: translateX(120%);
            transition: transform 0.3s ease-out;
        `;

        // Icon based on type
        const icon = document.createElement('span');
        icon.innerHTML = type === NOTIFICATION_TYPES.ERROR ? '⚠️' :
                        type === NOTIFICATION_TYPES.WARNING ? '⚡' : 'ℹ️';
        notification.appendChild(icon);

        // Message content
        const content = document.createElement('span');
        content.textContent = motorId ? `Motor ${motorId}: ${message}` : message;
        notification.appendChild(content);

        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = `
            margin-left: auto;
            background: none;
            border: none;
            color: #fff;
            font-size: 20px;
            cursor: pointer;
            padding: 0 5px;
        `;
        closeBtn.onclick = () => this.removeNotification(notification);
        notification.appendChild(closeBtn);

        // Add color based on type
        if (type === NOTIFICATION_TYPES.ERROR) {
            notification.style.borderLeft = '4px solid #ff4444';
        } else if (type === NOTIFICATION_TYPES.WARNING) {
            notification.style.borderLeft = '4px solid #ffbb00';
        } else {
            notification.style.borderLeft = '4px solid #4a9eff';
        }

        return notification;
    }

    show(message, type = NOTIFICATION_TYPES.INFO, motorId = null) {
        const notification = this.createNotification(message, type, motorId);
        this.container.appendChild(notification);

        // Trigger animation
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Auto-remove after timeout
        const timeoutId = setTimeout(() => {
            this.removeNotification(notification);
        }, NOTIFICATION_TIMEOUT);

        this.notifications.set(notification, timeoutId);
    }

    removeNotification(notification) {
        // Cancel timeout if exists
        const timeoutId = this.notifications.get(notification);
        if (timeoutId) {
            clearTimeout(timeoutId);
            this.notifications.delete(notification);
        }

        // Animate out
        notification.style.transform = 'translateX(120%)';
        setTimeout(() => {
            if (notification.parentNode === this.container) {
                this.container.removeChild(notification);
            }
        }, 300);
    }

    clearAll() {
        this.notifications.forEach((timeoutId, notification) => {
            clearTimeout(timeoutId);
            if (notification.parentNode === this.container) {
                this.container.removeChild(notification);
            }
        });
        this.notifications.clear();
    }
}

// Create global notification manager
window.notificationManager = new NotificationManager();

// Example usage:
// notificationManager.show('Temperature warning', 'warning', 3);
// notificationManager.show('High voltage detected', 'error', 2);
// notificationManager.show('Motor calibrated', 'info', 4);
