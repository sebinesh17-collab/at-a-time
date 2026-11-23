/**
 * AUTONOMOUSFORGE - Components Index
 * Export all reusable components
 */

import Sidebar from './Sidebar.js';
import Header from './Header.js';
import Card from './Card.js';
import Modal from './Modal.js';
import Table from './Table.js';
import Toast from './Toast.js';
import Form from './Form.js';

// Initialize toast system
Toast.init();

const Components = {
    Sidebar,
    Header,
    Card,
    Modal,
    Table,
    Toast,
    Form,
};

// Make available globally
window.AF.Components = Components;

export { Sidebar, Header, Card, Modal, Table, Toast, Form };
export default Components;