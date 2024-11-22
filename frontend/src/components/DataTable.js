import React, { useState } from 'react';

const DataTable = ({ data, onDataUpdate }) => {
  const [editingCell, setEditingCell] = useState(null);
  const [editValue, setEditValue] = useState('');

  const handleEdit = (rowId, field, value) => {
    setEditingCell({ rowId, field });
    setEditValue(value);
  };

  const handleSave = (rowId, field) => {
    const updatedData = data.map(row => {
      if (row.id === rowId) {
        return { ...row, [field]: editValue };
      }
      return row;
    });
    
    onDataUpdate(updatedData);
    setEditingCell(null);
    setEditValue('');
  };

  const renderCell = (row, field, value) => {
    const isEditing = editingCell?.rowId === row.id && editingCell?.field === field;
    const isEditableField = field === 'notes' || field === 'betterAnswer';

    if (isEditing) {
      return (
        <textarea
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={() => handleSave(row.id, field)}
          autoFocus
          className="edit-textarea"
        />
      );
    }

    return (
      <div
        onClick={() => isEditableField && handleEdit(row.id, field, value)}
        className={`cell-content ${isEditableField ? 'editable' : ''}`}
      >
        {value}
      </div>
    );
  };

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Input</th>
            <th>Expected Output</th>
            <th>Bot Output</th>
            <th>Notes</th>
            <th>Better Answer</th>
          </tr>
        </thead>
        <tbody>
          {data.map(row => (
            <tr key={row.id}>
              <td>{renderCell(row, 'input', row.input)}</td>
              <td>{renderCell(row, 'expectedOutput', row.expectedOutput)}</td>
              <td>{renderCell(row, 'botOutput', row.botOutput)}</td>
              <td>{renderCell(row, 'notes', row.notes)}</td>
              <td>{renderCell(row, 'betterAnswer', row.betterAnswer)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataTable;

