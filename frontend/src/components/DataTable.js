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
          className="w-full min-h-[24px] p-1 border border-blue-500 rounded resize-y focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      );
    }

    return (
      <div
        onClick={() => isEditableField && handleEdit(row.id, field, value)}
        className={`min-h-[24px] break-words ${isEditableField ? 'cursor-pointer hover:bg-gray-100' : ''}`}
      >
        {value}
      </div>
    );
  };

  return (
    <div className="m-5 overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="border border-gray-300 bg-gray-100 p-3 font-semibold text-left">Input</th>
            <th className="border border-gray-300 bg-gray-100 p-3 font-semibold text-left">Expected Output</th>
            <th className="border border-gray-300 bg-gray-100 p-3 font-semibold text-left">Bot Output</th>
            <th className="border border-gray-300 bg-gray-100 p-3 font-semibold text-left">Notes</th>
            <th className="border border-gray-300 bg-gray-100 p-3 font-semibold text-left">Better Answer</th>
          </tr>
        </thead>
        <tbody>
          {data.map(row => (
            <tr key={row.id} className="even:bg-gray-50 hover:bg-gray-100">
              <td className="border border-gray-300 p-3">{renderCell(row, 'input', row.input)}</td>
              <td className="border border-gray-300 p-3">{renderCell(row, 'expectedOutput', row.expectedOutput)}</td>
              <td className="border border-gray-300 p-3">{renderCell(row, 'botOutput', row.botOutput)}</td>
              <td className="border border-gray-300 p-3">{renderCell(row, 'notes', row.notes)}</td>
              <td className="border border-gray-300 p-3">{renderCell(row, 'betterAnswer', row.betterAnswer)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataTable;

